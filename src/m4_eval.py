"""M4: RAGAS evaluation (faithfulness, answer_relevancy, context_precision, context_recall).

LLM calls go through the OpenAI-compatible endpoint configured by OPENAI_BASE_URL /
OPENAI_API_KEY (Gemini in this team's setup). Embeddings run locally with BGE-M3.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import EMBEDDING_MODEL, JUDGE_MODEL, OPENAI_API_KEY

EVALUATOR_MODEL = os.getenv("EVALUATOR_MODEL", JUDGE_MODEL)
METRIC_NAMES = ("faithfulness", "answer_relevancy", "context_precision", "context_recall")
MAX_RETRY_PASSES = 2


def _build_llm():
    from langchain_core.outputs import ChatResult
    from langchain_openai import ChatOpenAI

    class SingleCompletionChat(ChatOpenAI):
        """Providers such as Gemini's OpenAI-compat API reject n>1; emulate it by looping."""

        @staticmethod
        def _merge(parts, model_name):
            generations, usage = [], {}
            for part in parts:
                generations.extend(part.generations)
                for key, value in (part.llm_output or {}).get("token_usage", {}).items():
                    if isinstance(value, (int, float)):
                        usage[key] = usage.get(key, 0) + value
            return ChatResult(generations=generations,
                              llm_output={"token_usage": usage, "model_name": model_name})

        def _generate(self, messages, stop=None, run_manager=None, **kwargs):
            n = kwargs.pop("n", None) or self.n or 1
            parts = [super(SingleCompletionChat, self)._generate(
                messages, stop=stop, run_manager=run_manager, n=1, **kwargs) for _ in range(n)]
            return self._merge(parts, self.model_name)

        async def _agenerate(self, messages, stop=None, run_manager=None, **kwargs):
            n = kwargs.pop("n", None) or self.n or 1
            parts = [await super(SingleCompletionChat, self)._agenerate(
                messages, stop=stop, run_manager=run_manager, n=1, **kwargs) for _ in range(n)]
            return self._merge(parts, self.model_name)

    return SingleCompletionChat(
        model=EVALUATOR_MODEL, temperature=0,
        api_key=os.getenv("EVALUATOR_API_KEY") or OPENAI_API_KEY,
        base_url=os.getenv("EVALUATOR_BASE_URL") or os.getenv("OPENAI_BASE_URL") or None,
        max_retries=6)


def _build_embeddings():
    from langchain_core.embeddings import Embeddings
    from src.m2_search import get_embedder

    class LocalBGE(Embeddings):
        def embed_documents(self, texts):
            return get_embedder().encode(list(texts), normalize_embeddings=True).tolist()

        def embed_query(self, text):
            return self.embed_documents([text])[0]

    return LocalBGE()


def _score(questions, answers, contexts, ground_truths, llm, embeddings) -> list[dict]:
    from datasets import Dataset
    from ragas import evaluate
    from ragas.embeddings import LangchainEmbeddingsWrapper
    from ragas.llms import LangchainLLMWrapper
    from ragas.metrics import answer_relevancy, context_precision, context_recall, faithfulness
    from ragas.run_config import RunConfig

    dataset = Dataset.from_dict({"question": list(questions), "answer": list(answers),
                                 "contexts": [list(c) for c in contexts],
                                 "ground_truth": list(ground_truths)})
    result = evaluate(
        dataset, metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
        llm=LangchainLLMWrapper(llm), embeddings=LangchainEmbeddingsWrapper(embeddings),
        run_config=RunConfig(timeout=240, max_retries=8, max_wait=90, max_workers=2),
        raise_exceptions=False)
    return result.to_pandas()[list(METRIC_NAMES)].to_dict("records")


def _is_bad(value) -> bool:
    return value is None or (isinstance(value, float) and math.isnan(value))


def _row_ok(row: dict) -> bool:
    return not any(_is_bad(row[m]) for m in METRIC_NAMES)


# Per-row cache so a provider quota stop (e.g. a free-tier daily limit) does not discard
# finished work. Each entry records the model that produced it; nothing is ever invented.
CACHE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                          ".ragas_cache", "rows.json")
BATCH_SIZE = 10


def _row_key(question, answer, contexts, ground_truth) -> str:
    raw = json.dumps([question, answer, list(contexts), ground_truth], ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _load_cache() -> dict:
    if os.path.exists(CACHE_PATH):
        with open(CACHE_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_cache(cache: dict) -> None:
    os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False)


def evaluate_ragas(questions: list[str], answers: list[str], contexts: list[list[str]],
                   ground_truths: list[str]) -> dict:
    """Return {"per_question": [obj with 4 float metrics], "metadata": {"evaluator_models": [...]}}.

    Rows are scored in small batches and cached as they complete. A row with NaN is re-scored
    up to MAX_RETRY_PASSES times; if any row is still missing, or a whole batch fails (provider
    quota/outage), the call raises and a rerun resumes from the cache. Scores are never invented.
    evaluator_models lists every model that produced a returned row, plus the embedding model.
    """
    n = len(questions)
    if not (n == len(answers) == len(contexts) == len(ground_truths)):
        raise ValueError("questions, answers, contexts, ground_truths must have the same length")
    keys = [_row_key(q, a, c, g) for q, a, c, g in zip(questions, answers, contexts, ground_truths)]
    cache = _load_cache()
    todo = [i for i, k in enumerate(keys) if k not in cache]
    print(f"[m4] {n - len(todo)}/{n} rows cached; scoring {len(todo)} with {EVALUATOR_MODEL}")
    llm, embeddings = (_build_llm(), _build_embeddings()) if todo else (None, None)

    for attempt in range(MAX_RETRY_PASSES + 1):
        todo = [i for i in todo if keys[i] not in cache]
        if not todo:
            break
        if attempt:
            print(f"[m4] retry {attempt}: re-scoring {len(todo)} rows with missing metrics")
        for start in range(0, len(todo), BATCH_SIZE):
            idx = todo[start:start + BATCH_SIZE]
            rows = _score([questions[i] for i in idx], [answers[i] for i in idx],
                          [contexts[i] for i in idx], [ground_truths[i] for i in idx], llm, embeddings)
            good = 0
            for i, row in zip(idx, rows):
                if _row_ok(row):
                    cache[keys[i]] = {**{m: float(row[m]) for m in METRIC_NAMES},
                                      "model": EVALUATOR_MODEL}
                    good += 1
            _save_cache(cache)
            print(f"[m4] batch {start // BATCH_SIZE + 1}: {good}/{len(idx)} rows ok")
            if good == 0:
                raise RuntimeError("A whole batch failed (provider quota/outage?). Progress is cached "
                                   "in .ragas_cache; rerun later or set another EVALUATOR_MODEL.")

    missing = [i for i, k in enumerate(keys) if k not in cache]
    if missing:
        raise ValueError(f"RAGAS missing rows {missing} after retries; progress cached, rerun.")

    entries = [cache[k] for k in keys]
    per_question = [SimpleNamespace(**{m: float(e[m]) for m in METRIC_NAMES}) for e in entries]
    means = {m: sum(getattr(p, m) for p in per_question) / n for m in METRIC_NAMES}
    models = sorted({e["model"] for e in entries}) + [EMBEDDING_MODEL]
    return {"per_question": per_question, "aggregate": means,
            "metadata": {"evaluator_models": models}}
