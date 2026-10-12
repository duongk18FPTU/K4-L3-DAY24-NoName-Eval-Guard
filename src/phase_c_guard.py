from __future__ import annotations

"""Phase C: Production Guardrails — Presidio PII + NeMo Guardrails + P95 Latency."""

import asyncio
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import GUARDRAILS_CONFIG_DIR, PRESIDIO_LANGUAGE


# ─── Task 9a: Presidio PII Detection ─────────────────────────────────────────

def setup_presidio():
    """Khởi tạo Presidio engine với custom Vietnamese PII recognizers. (Đã implement sẵn)

    Custom recognizers thêm vào:
        VN_CCCD  — số CCCD 12 chữ số hoặc CMND 9 chữ số
        VN_PHONE — số điện thoại Việt Nam (0[3-9]xxxxxxxx)

    Các recognizers mặc định đã có sẵn: EMAIL, PHONE_NUMBER (international), ...
    """
    from presidio_analyzer import AnalyzerEngine, RecognizerRegistry, Pattern, PatternRecognizer
    from presidio_anonymizer import AnonymizerEngine

    cccd_recognizer = PatternRecognizer(
        supported_entity="VN_CCCD",
        patterns=[
            Pattern("CCCD 12 digits", r"\b\d{12}\b", 0.9),
            Pattern("CMND 9 digits",  r"\b\d{9}\b",  0.7),
        ],
    )
    phone_recognizer = PatternRecognizer(
        supported_entity="VN_PHONE",
        patterns=[Pattern("VN mobile", r"\b0[3-9]\d{8}\b", 0.9)],
    )

    registry = RecognizerRegistry()
    registry.load_predefined_recognizers()
    registry.add_recognizer(cccd_recognizer)
    registry.add_recognizer(phone_recognizer)

    analyzer  = AnalyzerEngine(registry=registry)
    anonymizer = AnonymizerEngine()
    return analyzer, anonymizer


def pii_scan(text: str, analyzer=None, anonymizer=None) -> dict:
    """Detect and anonymize PII, preserving entity offsets in the original text."""
    if analyzer is None or anonymizer is None:
        default_analyzer, default_anonymizer = setup_presidio()
        analyzer = default_analyzer if analyzer is None else analyzer
        anonymizer = default_anonymizer if anonymizer is None else anonymizer
    # The English NER model mislabels Vietnamese policy text as PERSON/LOCATION.
    # This layer covers the lab's identifiers; semantic privacy requests go to NeMo.
    supported_entities = {"VN_CCCD", "VN_PHONE", "EMAIL_ADDRESS", "PHONE_NUMBER"}
    results = [r for r in analyzer.analyze(text=text, language=PRESIDIO_LANGUAGE)
               if r.entity_type in supported_entities]
    if not results:
        return {"has_pii": False, "entities": [], "anonymized": text}
    entities = [{"type": r.entity_type, "text": text[r.start:r.end],
                 "score": float(r.score), "start": r.start, "end": r.end} for r in results]
    anonymized = anonymizer.anonymize(text=text, analyzer_results=results).text
    return {"has_pii": True, "entities": entities, "anonymized": anonymized}


# ─── Task 9b + 11: NeMo Guardrails ───────────────────────────────────────────

def setup_nemo_rails():
    """Khởi tạo NeMo Guardrails từ guardrails/config.yml. (Đã implement sẵn)

    Config directory: guardrails/
        config.yml  — model + rails config
        rails.co    — câu từ chối Colang 1.0; built-in self-check flows được bật trong YAML
    """
    from nemoguardrails import RailsConfig, LLMRails
    from langchain_openai import ChatOpenAI
    config = RailsConfig.from_path(GUARDRAILS_CONFIG_DIR)
    # NeMo 0.10 selects chat only for gpt-3.5/gpt-4 names; OpenRouter slugs
    # require an explicit chat client to avoid its legacy completions provider.
    main = next(model for model in config.models if model.type == "main")
    llm = ChatOpenAI(model=main.model, **main.parameters)
    rails = LLMRails(config, llm=llm)
    return rails


async def check_input_rail(text: str, rails=None) -> dict:
    """Run only input rails and use the logged rail decision."""
    if rails is None:
        rails = setup_nemo_rails()
    result = await rails.generate_async(
        messages=[{"role": "user", "content": text}],
        options={"rails": ["input"], "log": {"activated_rails": True}},
    )
    blocked = any(rail.stop for rail in result.log.activated_rails)
    return {"allowed": not blocked, "blocked_reason": "nemo_input_rail" if blocked else None,
            "response": result.response[0]["content"]}


async def check_output_rail(question: str, answer: str, rails=None) -> dict:
    """Check a supplied answer with output rails; preserve safe answers exactly."""
    if rails is None:
        rails = setup_nemo_rails()
    result = await rails.generate_async(
        messages=[{"role": "user", "content": question},
                  {"role": "assistant", "content": answer}],
        options={"rails": ["output"], "log": {"activated_rails": True}},
    )
    flagged = any(rail.stop for rail in result.log.activated_rails)
    return {"safe": not flagged, "flagged_reason": "nemo_output_rail" if flagged else None,
            "final_answer": result.response[0]["content"] if flagged else answer}


# ─── Task 10: Adversarial Test Suite ─────────────────────────────────────────

def run_adversarial_suite(adversarial_set: list[dict], rails=None,
                           analyzer=None, anonymizer=None) -> list[dict]:
    """Run arbitrary inputs; expected labels are used only after guard decisions."""
    if not adversarial_set:
        return []
    if analyzer is None or anonymizer is None:
        default_analyzer, default_anonymizer = setup_presidio()
        analyzer = default_analyzer if analyzer is None else analyzer
        anonymizer = default_anonymizer if anonymizer is None else anonymizer
    if rails is None:
        rails = setup_nemo_rails()
    async def run_all():
        rows = []
        for item in adversarial_set:
            blocked_by = None
            if pii_scan(item["input"], analyzer, anonymizer)["has_pii"]:
                blocked_by = "presidio"
            elif not (await check_input_rail(item["input"], rails))["allowed"]:
                blocked_by = "nemo_input"
            actual = "blocked" if blocked_by else "allowed"
            rows.append({"id": item["id"], "category": item["category"],
                         "input": item["input"], "expected": item["expected"],
                         "actual": actual, "blocked_by": blocked_by,
                         "passed": actual == item["expected"]})
        return rows
    return asyncio.run(run_all())


# ─── Task 12: P95 Latency Measurement ────────────────────────────────────────

def measure_p95_latency(test_inputs: list[str], n_runs: int = 20,
                         rails=None, analyzer=None, anonymizer=None) -> dict:
    """Measure both input layers sequentially, excluding two real warm-up calls."""
    from src.experiment_support import summarize_latency
    if not test_inputs or type(n_runs) is not int or n_runs < 20:
        raise ValueError("Need inputs and at least 20 timed samples.")
    if analyzer is None or anonymizer is None:
        default_analyzer, default_anonymizer = setup_presidio()
        analyzer = default_analyzer if analyzer is None else analyzer
        anonymizer = default_anonymizer if anonymizer is None else anonymizer
    if rails is None:
        rails = setup_nemo_rails()
    async def measure():
        for i in range(2):
            text = test_inputs[i % len(test_inputs)]
            pii_scan(text, analyzer, anonymizer)
            await check_input_rail(text, rails)
        samples = []
        for i in range(n_runs):
            text = test_inputs[i % len(test_inputs)]
            start = time.perf_counter()
            pii_scan(text, analyzer, anonymizer)
            pii_ms = (time.perf_counter() - start) * 1000
            start = time.perf_counter()
            await check_input_rail(text, rails)
            nemo_ms = (time.perf_counter() - start) * 1000
            samples.append({"presidio_ms": pii_ms, "nemo_input_ms": nemo_ms,
                            "input_guard_ms": pii_ms + nemo_ms})
        return samples
    return summarize_latency(asyncio.run(measure()), warmup_runs=2)


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from scripts.run_experiments import main
    raise SystemExit(main(["--phase", "c", *sys.argv[1:]]))
