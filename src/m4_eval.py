"""M4: RAGAS evaluation (faithfulness, answer_relevancy, context_precision, context_recall).

LLM calls go through the OpenAI-compatible endpoint configured by OPENAI_BASE_URL /
OPENAI_API_KEY (Gemini in this team's setup). Embeddings run locally with BGE-M3.
"""
from __future__ import annotations

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

        def _generate(self, messages, stop=None, run_manager=None, **kwargs):
            n = kwargs.pop("n", None) or self.n or 1
            kwargs.pop("n", None)
            generations, usage = [], {}
            for _ in range(n):
                part = super()._generate(messages, stop=stop, run_manager=run_manager, n=1, **kwargs)
                generations.extend(part.generations)
                for key, value in (part.llm_output or {}).get("token_usage", {}).items():
                    if isinstance(value, (int, float)):
                        usage[key] = usage.get(key, 0) + value
            return ChatResult(generations=generations,
                              llm_output={"token_usage": usage, "model_name": self.model_name})

    return SingleCompletionChat(model=EVALUATOR_MODEL, temperature=0, api_key=OPENAI_API_KEY,
                                base_url=os.getenv("OPENAI_BASE_URL") or None, max_retries=6)


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
        raise_exceptions=False, show_progress=True)
    return result.to_pandas()[list(METRIC_NAMES)].to_dict("records")


def _is_bad(value) -> bool:
    return value is None or (isinstance(value, float) and math.isnan(value))


def evaluate_ragas(questions: list[str], answers: list[str], contexts: list[list[str]],
                   ground_truths: list[str]) -> dict:
    """Return {"per_question": [obj with 4 float metrics], "metadata": {"evaluator_models": [...]}}.

    Rows where RAGAS produced NaN (provider errors/rate limits) are re-scored on their own up to
    MAX_RETRY_PASSES times; if NaN remains the call fails instead of inventing a score.
    """
    n = len(questions)
    if not (n == len(answers) == len(contexts) == len(ground_truths)):
        raise ValueError("questions, answers, contexts, ground_truths must have the same length")
    llm, embeddings = _build_llm(), _build_embeddings()
    rows = _score(questions, answers, contexts, ground_truths, llm, embeddings)

    for attempt in range(1, MAX_RETRY_PASSES + 1):
        bad = [i for i, row in enumerate(rows) if any(_is_bad(row[m]) for m in METRIC_NAMES)]
        if not bad:
            break
        print(f"[m4] retry {attempt}: re-scoring {len(bad)} rows with missing metrics")
        redo = _score([questions[i] for i in bad], [answers[i] for i in bad],
                      [contexts[i] for i in bad], [ground_truths[i] for i in bad], llm, embeddings)
        for i, row in zip(bad, redo):
            rows[i] = {m: (row[m] if _is_bad(rows[i][m]) else rows[i][m]) for m in METRIC_NAMES}

    still_bad = [i for i, row in enumerate(rows) if any(_is_bad(row[m]) for m in METRIC_NAMES)]
    if still_bad:
        raise ValueError(f"RAGAS returned NaN for rows {still_bad} after retries; rerun later.")

    per_question = [SimpleNamespace(**{m: float(row[m]) for m in METRIC_NAMES}) for row in rows]
    means = {m: sum(getattr(p, m) for p in per_question) / n for m in METRIC_NAMES}
    return {"per_question": per_question, "aggregate": means,
            "metadata": {"evaluator_models": [EVALUATOR_MODEL, EMBEDDING_MODEL]}}
