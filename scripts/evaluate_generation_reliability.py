"""Compare raw JSON acceptance with LearnLoop's validation and repair loop."""

import argparse
import hashlib
import json
import os
import platform
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.schemas import FlashcardOutput, QuizOutput

MODEL = "gpt-4o-mini"
MAX_REPAIR_RETRIES = 2


def strip_json_fence(raw_output: str) -> str:
    text = raw_output.strip()
    if text.startswith("```"):
        first_line, separator, remainder = text.partition("\n")
        if separator and first_line[3:].strip().lower() in {"", "json"}:
            text = remainder
        if text.rstrip().endswith("```"):
            text = text.rstrip()[:-3]
    return text.strip()


def validation_error(raw_output: str, case: dict) -> str | None:
    try:
        parsed = json.loads(strip_json_fence(raw_output))
        if case["type"] == "quiz":
            validated = QuizOutput.model_validate(parsed)
            count = len(validated.quiz)
        else:
            normalized = {"flashcards": parsed} if isinstance(parsed, list) else parsed
            validated = FlashcardOutput.model_validate(normalized)
            count = len(validated.flashcards)
        if count != case["count"]:
            return f"Expected exactly {case['count']} items, got {count}"
    except (json.JSONDecodeError, ValidationError, TypeError, ValueError) as exc:
        return str(exc)
    return None


def prompts(case: dict) -> tuple[str, str]:
    if case["type"] == "quiz":
        system_prompt = (
            "You are an AI quiz generator. Respond with exactly one JSON object and nothing else. "
            f"Produce exactly {case['count']} questions. Include a mix of MCQ, True/False, and Fill-in-the-blank questions. "
            "For MCQ questions, provide exactly four options and a correct answer letter. "
            "For every question, provide type, question, correct_answer, and explanation. "
            "Return one JSON object with a quiz key."
        )
        user_prompt = f"Here is study material:\n\n{case['content']}\n"
    else:
        system_prompt = (
            "You are an AI flashcard generator. Respond with only one JSON object and no extra text. "
            f"Generate exactly {case['count']} flashcards using the study material. "
            "Each flashcard must have a term and definition. Return one JSON object with a flashcards key."
        )
        user_prompt = f"Study material:\n\n{case['content']}\n"
    return system_prompt, user_prompt


def call_model(client: OpenAI, system_prompt: str, user_prompt: str) -> str:
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=800,
        temperature=0.7,
    )
    return (response.choices[0].message.content or "").strip()


def percentile(values: list[float], percentile_value: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * percentile_value / 100
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return round(ordered[lower] + (ordered[upper] - ordered[lower]) * fraction, 4)


def run(dataset_path: Path, report_path: Path) -> dict:
    dataset_path = dataset_path.resolve()
    dataset_bytes = dataset_path.read_bytes()
    dataset = json.loads(dataset_bytes)
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    cases = []
    baseline_latencies = []
    robust_latencies = []
    total_model_calls = 0

    for case in dataset["cases"]:
        system_prompt, user_prompt = prompts(case)
        started = time.perf_counter()
        result = {
            "id": case["id"],
            "type": case["type"],
            "count": case["count"],
            "baseline_first_pass_valid": False,
            "final_valid": False,
            "repair_attempts": 0,
        }
        try:
            raw_output = call_model(client, system_prompt, user_prompt)
            total_model_calls += 1
            baseline_latency_ms = (time.perf_counter() - started) * 1000
            baseline_error = validation_error(raw_output, case)
            result["baseline_first_pass_valid"] = baseline_error is None
            result["baseline_error"] = baseline_error
            baseline_latencies.append(baseline_latency_ms)

            prompt = user_prompt
            last_error = baseline_error
            for attempt in range(MAX_REPAIR_RETRIES + 1):
                if attempt == 0 and baseline_error is None:
                    result["final_valid"] = True
                    break
                if attempt > 0:
                    prompt = (
                        f"{user_prompt}\n\nYour previous output was invalid. Return only corrected JSON. "
                        f"Validation feedback: {last_error}\nPrevious output: {raw_output}"
                    )
                    raw_output = call_model(client, system_prompt, prompt)
                    total_model_calls += 1
                result["repair_attempts"] = attempt
                last_error = validation_error(raw_output, case)
                if last_error is None:
                    result["final_valid"] = True
                    break
            result["final_error"] = last_error
            result["elapsed_latency_ms"] = round((time.perf_counter() - started) * 1000, 3)
            robust_latencies.append(result["elapsed_latency_ms"])
        except Exception as exc:
            result["provider_error"] = f"{type(exc).__name__}: {exc}"
            result["final_error"] = result["provider_error"]
            result["elapsed_latency_ms"] = round((time.perf_counter() - started) * 1000, 3)
            robust_latencies.append(result["elapsed_latency_ms"])
        cases.append(result)

    case_count = len(cases)
    baseline_valid = sum(case["baseline_first_pass_valid"] for case in cases)
    final_valid = sum(case["final_valid"] for case in cases)
    repaired = sum(case["repair_attempts"] > 0 for case in cases)
    repair_successes = sum(
        case["repair_attempts"] > 0 and case["final_valid"] for case in cases
    )
    report = {
        "benchmark": "LearnLoop generation validation and repair reliability",
        "model": MODEL,
        "dataset": str(dataset_path.relative_to(ROOT)),
        "dataset_sha256": hashlib.sha256(dataset_bytes).hexdigest(),
        "case_count": case_count,
        "baseline_definition": "same first model response scored with JSON parsing, schema validation, and exact item-count checks, without repair",
        "robust_definition": "same first response plus Pydantic validation and at most two repair retries",
        "metrics": {
            "baseline_first_pass_valid": baseline_valid,
            "baseline_first_pass_valid_rate": baseline_valid / case_count,
            "robust_final_valid": final_valid,
            "robust_final_valid_rate": final_valid / case_count,
            "repaired_cases": repaired,
            "repair_case_rate": repaired / case_count,
            "repair_successes": repair_successes,
            "final_failures": case_count - final_valid,
            "final_failure_rate": (case_count - final_valid) / case_count,
            "baseline_p50_latency_ms": percentile(baseline_latencies, 50),
            "robust_p50_latency_ms": percentile(robust_latencies, 50),
            "total_model_calls": total_model_calls,
        },
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
        },
        "command": "PYTHONPATH=backend python3.11 scripts/evaluate_generation_reliability.py --dataset docs/benchmarks/generation_reliability_corpus.json --report docs/benchmarks/generation_reliability_report.json --env-file backend/.env",
        "cases": cases,
    }
    report_path = report_path.resolve()
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare raw generation with LearnLoop repair reliability.")
    parser.add_argument("--dataset", type=Path, default=ROOT / "docs/benchmarks/generation_reliability_corpus.json")
    parser.add_argument("--report", type=Path, default=ROOT / "docs/benchmarks/generation_reliability_report.json")
    parser.add_argument("--env-file", type=Path, default=ROOT / "backend/.env")
    args = parser.parse_args()
    load_dotenv(args.env_file)
    if not os.getenv("OPENAI_API_KEY"):
        parser.error("OPENAI_API_KEY is required")
    report = run(args.dataset, args.report)
    print(json.dumps({"report": str(args.report), "metrics": report["metrics"]}, indent=2))


if __name__ == "__main__":
    main()
