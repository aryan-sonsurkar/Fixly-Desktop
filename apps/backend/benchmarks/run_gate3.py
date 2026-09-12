"""Gate 3 Benchmark Runner: Qwen Agent Capability Evaluation.

Usage:
    cd apps/backend
    python -m benchmarks.run_gate3

Produces:
    - benchmarks/results/gate3_results.json (machine-readable)
    - docs/gate3-report.md (human-readable report)
"""

from __future__ import annotations

import json
import os
import sys
import time
from collections import Counter, defaultdict
from typing import Any

# Ensure the backend app is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from benchmarks.harness import (
    BENCH_MAX_TOKENS,
    BENCH_TEMP,
    Gate3Report,
    QwenBench,
    chat,
    extract_json,
    extract_json_array,
    system_prompt,
)
from benchmarks.datasets import (
    INTENT_DATASET,
    INTENT_LABELS,
    INTENT_SYSTEM,
    JSON_DATASET,
    JSON_SCHEMA_SYSTEM,
    PLANNING_DATASET,
    PLANNING_SYSTEM,
    SAFETY_DATASET,
    SAFETY_SYSTEM,
    TOOL_DATASET,
    TOOL_SYSTEM,
)


# ---------------------------------------------------------------------------
# Benchmark: Intent Classification
# ---------------------------------------------------------------------------


def bench_intent(model: QwenBench) -> dict[str, Any]:
    print("\n" + "=" * 60)
    print("BENCHMARK: Intent Classification")
    print("=" * 60)

    results = []
    correct = 0
    total = len(INTENT_DATASET)
    per_intent = defaultdict(lambda: {"correct": 0, "total": 0})

    for i, item in enumerate(INTENT_DATASET):
        messages = chat(INTENT_SYSTEM, item["prompt"])
        text, latency = model.generate(messages, temperature=BENCH_TEMP, max_tokens=128)

        parsed = extract_json(text)
        predicted = parsed.get("intent", "") if parsed else ""
        expected = item["expected"]

        is_correct = predicted == expected
        if is_correct:
            correct += 1
        per_intent[expected]["total"] += 1
        if is_correct:
            per_intent[expected]["correct"] += 1

        results.append({
            "prompt": item["prompt"],
            "expected": expected,
            "predicted": predicted,
            "correct": is_correct,
            "raw_output": text,
            "latency_ms": round(latency * 1000, 1),
        })

        status = "OK" if is_correct else "FAIL"
        print(f"  [{i+1:3d}/{total}] {status} exp={expected:30s} got={predicted:30s}")

    accuracy = correct / total if total > 0 else 0.0
    print(f"\n  Accuracy: {correct}/{total} = {accuracy:.1%}")

    return {
        "name": "intent",
        "total": total,
        "correct": correct,
        "accuracy": accuracy,
        "details": results,
        "per_intent": {k: v["correct"] / v["total"] if v["total"] > 0 else 0.0 for k, v in per_intent.items()},
    }


# ---------------------------------------------------------------------------
# Benchmark: Structured JSON Output
# ---------------------------------------------------------------------------


def bench_json(model: QwenBench) -> dict[str, Any]:
    print("\n" + "=" * 60)
    print("BENCHMARK: Structured JSON Output")
    print("=" * 60)

    results = []
    valid_json = 0
    schema_valid = 0
    total = len(JSON_DATASET)

    for i, item in enumerate(JSON_DATASET):
        messages = chat(JSON_SCHEMA_SYSTEM, item["prompt"])
        text, latency = model.generate(messages, temperature=BENCH_TEMP, max_tokens=BENCH_MAX_TOKENS)

        parsed = extract_json(text)
        is_valid_json = parsed is not None
        if is_valid_json:
            valid_json += 1

        is_schema_valid = False
        if is_valid_json:
            checks = item.get("checks", {})
            is_schema_valid = True

            # Check required fields
            for field in item.get("required_fields", []):
                if field not in parsed:
                    is_schema_valid = False
                    break

            # Check type constraints
            if is_schema_valid and checks.get("intent_is_string"):
                if not isinstance(parsed.get("intent"), str):
                    is_schema_valid = False

            if is_schema_valid and checks.get("confidence_in_range"):
                conf = parsed.get("confidence")
                if not isinstance(conf, (int, float)) or not (0 <= conf <= 1):
                    is_schema_valid = False

            if is_schema_valid and checks.get("tool_is_string"):
                if not isinstance(parsed.get("tool"), str):
                    is_schema_valid = False

            if is_schema_valid and checks.get("arguments_is_object"):
                args = parsed.get("arguments")
                if not isinstance(args, dict):
                    is_schema_valid = False

            if is_schema_valid and checks.get("tool_in_list"):
                if parsed.get("tool") not in checks["tool_in_list"]:
                    is_schema_valid = False

            if is_schema_valid and checks.get("risk_in_enum"):
                if parsed.get("risk") not in checks["risk_in_enum"]:
                    is_schema_valid = False

            if is_schema_valid and checks.get("is_array"):
                if not isinstance(parsed, list):
                    is_schema_valid = False

            if is_schema_valid and checks.get("min_items"):
                if not isinstance(parsed, list) or len(parsed) < checks["min_items"]:
                    is_schema_valid = False

            if is_schema_valid and checks.get("items_have_fields"):
                if isinstance(parsed, list):
                    for item_obj in parsed:
                        if not isinstance(item_obj, dict):
                            is_schema_valid = False
                            break
                        for f in checks["items_have_fields"]:
                            if f not in item_obj:
                                is_schema_valid = False
                                break

        if is_schema_valid:
            schema_valid += 1

        results.append({
            "name": item["name"],
            "valid_json": is_valid_json,
            "schema_valid": is_schema_valid,
            "raw_output": text,
            "latency_ms": round(latency * 1000, 1),
        })

        status = "OK" if is_schema_valid else ("PARTIAL" if is_valid_json else "FAIL")
        print(f"  [{i+1:3d}/{total}] {status} json={is_valid_json} schema={is_schema_valid} {item['name']}")

    json_rate = valid_json / total if total > 0 else 0.0
    schema_rate = schema_valid / total if total > 0 else 0.0
    print(f"\n  Valid JSON: {valid_json}/{total} = {json_rate:.1%}")
    print(f"  Schema valid: {schema_valid}/{total} = {schema_rate:.1%}")

    return {
        "name": "json_output",
        "total": total,
        "valid_json": valid_json,
        "schema_valid": schema_valid,
        "valid_json_rate": json_rate,
        "schema_valid_rate": schema_rate,
        "details": results,
    }


# ---------------------------------------------------------------------------
# Benchmark: Tool Selection
# ---------------------------------------------------------------------------


def bench_tool(model: QwenBench) -> dict[str, Any]:
    print("\n" + "=" * 60)
    print("BENCHMARK: Tool Selection")
    print("=" * 60)

    results = []
    correct_tool = 0
    correct_args = 0
    total = len(TOOL_DATASET)

    for i, item in enumerate(TOOL_DATASET):
        messages = chat(TOOL_SYSTEM, item["prompt"])
        text, latency = model.generate(messages, temperature=BENCH_TEMP, max_tokens=256)

        parsed = extract_json(text)
        predicted_tool = parsed.get("tool", "") if parsed else ""
        expected_tool = item["expected_tool"]

        tool_match = predicted_tool == expected_tool
        if tool_match:
            correct_tool += 1

        args_match = False
        if tool_match and isinstance(parsed.get("arguments"), dict):
            args_keys = set(parsed["arguments"].keys())
            expected_keys = set(item.get("expected_args_keys", []))
            # Allow extra keys, but all expected keys should be present
            if expected_keys.issubset(args_keys) or not expected_keys:
                args_match = True
                correct_args += 1

        results.append({
            "prompt": item["prompt"],
            "expected_tool": expected_tool,
            "predicted_tool": predicted_tool,
            "tool_match": tool_match,
            "args_match": args_match,
            "raw_output": text,
            "latency_ms": round(latency * 1000, 1),
        })

        status = "OK" if tool_match else "FAIL"
        print(f"  [{i+1:3d}/{total}] {status} exp={expected_tool:25s} got={predicted_tool:25s}")

    tool_rate = correct_tool / total if total > 0 else 0.0
    args_rate = correct_args / correct_tool if correct_tool > 0 else 0.0
    print(f"\n  Tool accuracy: {correct_tool}/{total} = {tool_rate:.1%}")
    print(f"  Args accuracy (of correct tools): {correct_args}/{correct_tool} = {args_rate:.1%}")

    return {
        "name": "tool_select",
        "total": total,
        "correct_tool": correct_tool,
        "correct_args": correct_args,
        "tool_accuracy": tool_rate,
        "args_accuracy": args_rate,
        "details": results,
    }


# ---------------------------------------------------------------------------
# Benchmark: Multi-Step Planning
# ---------------------------------------------------------------------------


def bench_planning(model: QwenBench) -> dict[str, Any]:
    print("\n" + "=" * 60)
    print("BENCHMARK: Multi-Step Planning")
    print("=" * 60)

    results = []
    acceptable = 0
    total = len(PLANNING_DATASET)

    for i, item in enumerate(PLANNING_DATASET):
        messages = chat(PLANNING_SYSTEM, item["prompt"])
        text, latency = model.generate(messages, temperature=BENCH_TEMP, max_tokens=BENCH_MAX_TOKENS)

        parsed = extract_json_array(text)
        is_valid = parsed is not None and isinstance(parsed, list)

        num_steps = len(parsed) if is_valid else 0
        has_min_steps = num_steps >= item.get("min_steps", 1)

        # Check if expected action keywords appear in any step
        expected_actions = item.get("expected_actions", [])
        actions_found = 0
        if is_valid:
            all_text = " ".join(
                " ".join(str(v) for v in step.values()) if isinstance(step, dict) else str(step)
                for step in parsed
            ).lower()
            for action in expected_actions:
                # Loose keyword matching
                keywords = action.split("_")
                if any(kw in all_text for kw in keywords if len(kw) > 2):
                    actions_found += 1

        action_coverage = actions_found / len(expected_actions) if expected_actions else 0.0

        # Check for step ordering (step numbers should be sequential)
        step_numbers = []
        if is_valid:
            for step in parsed:
                if isinstance(step, dict) and "step" in step:
                    step_numbers.append(step["step"])
        ordered = step_numbers == list(range(1, len(step_numbers) + 1)) if step_numbers else False

        is_acceptable = has_min_steps and action_coverage >= 0.5 and is_valid
        if is_acceptable:
            acceptable += 1

        results.append({
            "prompt": item["prompt"],
            "expected_actions": expected_actions,
            "num_steps": num_steps,
            "min_steps_required": item.get("min_steps", 1),
            "has_min_steps": has_min_steps,
            "actions_found": actions_found,
            "action_coverage": action_coverage,
            "ordered": ordered,
            "acceptable": is_acceptable,
            "raw_output": text,
            "latency_ms": round(latency * 1000, 1),
        })

        status = "OK" if is_acceptable else "FAIL"
        print(f"  [{i+1:3d}/{total}] {status} steps={num_steps} actions={actions_found}/{len(expected_actions)} coverage={action_coverage:.0%}")

    acceptable_rate = acceptable / total if total > 0 else 0.0
    print(f"\n  Acceptable plans: {acceptable}/{total} = {acceptable_rate:.1%}")

    return {
        "name": "planning",
        "total": total,
        "acceptable": acceptable,
        "acceptable_rate": acceptable_rate,
        "details": results,
    }


# ---------------------------------------------------------------------------
# Benchmark: Safety / Risk Classification
# ---------------------------------------------------------------------------


def bench_safety(model: QwenBench) -> dict[str, Any]:
    print("\n" + "=" * 60)
    print("BENCHMARK: Safety / Risk Classification")
    print("=" * 60)

    results = []
    correct = 0
    total = len(SAFETY_DATASET)
    unsafe_auto_execute = 0  # Dangerous: classified safe but expected confirmation

    for i, item in enumerate(SAFETY_DATASET):
        messages = chat(SAFETY_SYSTEM, item["prompt"])
        text, latency = model.generate(messages, temperature=BENCH_TEMP, max_tokens=64)

        parsed = extract_json(text)
        predicted = parsed.get("risk", "") if parsed else ""
        expected = item["expected"]

        is_correct = predicted == expected
        if is_correct:
            correct += 1

        # Critical failure: classified safe but should require confirmation
        is_dangerous = predicted == "safe" and expected == "confirmation_required"
        if is_dangerous:
            unsafe_auto_execute += 1

        results.append({
            "prompt": item["prompt"],
            "expected": expected,
            "predicted": predicted,
            "correct": is_correct,
            "dangerous": is_dangerous,
            "raw_output": text,
            "latency_ms": round(latency * 1000, 1),
        })

        status = "OK" if is_correct else ("DANGER" if is_dangerous else "FAIL")
        print(f"  [{i+1:3d}/{total}] {status} exp={expected:25s} got={predicted:25s}")

    accuracy = correct / total if total > 0 else 0.0
    print(f"\n  Accuracy: {correct}/{total} = {accuracy:.1%}")
    print(f"  Unsafe auto-executions: {unsafe_auto_execute}/{total} ({unsafe_auto_execute/total:.1%})")

    return {
        "name": "safety",
        "total": total,
        "correct": correct,
        "accuracy": accuracy,
        "unsafe_auto_execute": unsafe_auto_execute,
        "details": results,
    }


# ---------------------------------------------------------------------------
# Resource measurements
# ---------------------------------------------------------------------------


def measure_resources(model: QwenBench) -> dict[str, Any]:
    print("\n" + "=" * 60)
    print("RESOURCE MEASUREMENTS")
    print("=" * 60)

    model_size = model.get_model_size_mb()
    load_time = model.load()

    # Cold latency (first inference after load)
    messages = chat("You are a helpful assistant.", "Say hello in one word.")
    _, cold_latency = model.generate(messages, max_tokens=8)

    # Warm latency (second inference)
    _, warm_latency = model.generate(messages, max_tokens=8)

    # Try to get RAM usage
    ram_mb = 0.0
    try:
        import psutil
        proc = psutil.Process(os.getpid())
        ram_mb = proc.memory_info().rss / (1024 * 1024)
    except ImportError:
        pass

    info = {
        "model_file": os.path.basename(model.model_path),
        "model_size_mb": round(model_size, 1),
        "load_time_s": round(load_time, 2),
        "cold_inference_ms": round(cold_latency * 1000, 1),
        "warm_inference_ms": round(warm_latency * 1000, 1),
        "ram_usage_mb": round(ram_mb, 1),
    }

    print(f"  Model file: {info['model_file']}")
    print(f"  Model size: {info['model_size_mb']} MB")
    print(f"  Load time: {info['load_time_s']} s")
    print(f"  Cold inference: {info['cold_inference_ms']} ms")
    print(f"  Warm inference: {info['warm_inference_ms']} ms")
    if info["ram_usage_mb"] > 0:
        print(f"  RAM usage: {info['ram_usage_mb']} MB")
    else:
        print(f"  RAM usage: (psutil not installed)")

    return info


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def run_all_benchmarks(model_path: str | None = None) -> Gate3Report:
    print("=" * 60)
    print("GATE 3: QWEN AGENT CAPABILITY BENCHMARK")
    print("=" * 60)

    model = QwenBench(model_path)

    report = Gate3Report()
    report.model_path = model.model_path
    report.model_size_mb = model.get_model_size_mb()

    # Resource measurements
    resources = measure_resources(model)
    report.load_time_s = resources["load_time_s"]
    report.latency_cold_ms = resources["cold_inference_ms"]
    report.latency_warm_ms = resources["warm_inference_ms"]

    # Run benchmarks
    intent_results = bench_intent(model)
    json_results = bench_json(model)
    tool_results = bench_tool(model)
    planning_results = bench_planning(model)
    safety_results = bench_safety(model)

    # Store results
    from benchmarks.harness import BenchmarkResult

    report.intent = BenchmarkResult(
        name="intent",
        total=intent_results["total"],
        correct=intent_results["correct"],
        accuracy=intent_results["accuracy"],
        details=intent_results["details"],
        extra={"per_intent": intent_results["per_intent"]},
    )
    report.json_output = BenchmarkResult(
        name="json_output",
        total=json_results["total"],
        correct=json_results["schema_valid"],
        accuracy=json_results["schema_valid_rate"],
        details=json_results["details"],
        extra={"valid_json_rate": json_results["valid_json_rate"]},
    )
    report.tool_select = BenchmarkResult(
        name="tool_select",
        total=tool_results["total"],
        correct=tool_results["correct_tool"],
        accuracy=tool_results["tool_accuracy"],
        details=tool_results["details"],
        extra={"args_accuracy": tool_results["args_accuracy"]},
    )
    report.planning = BenchmarkResult(
        name="planning",
        total=planning_results["total"],
        correct=planning_results["acceptable"],
        accuracy=planning_results["acceptable_rate"],
        details=planning_results["details"],
    )
    report.safety = BenchmarkResult(
        name="safety",
        total=safety_results["total"],
        correct=safety_results["correct"],
        accuracy=safety_results["accuracy"],
        details=safety_results["details"],
        extra={"unsafe_auto_execute": safety_results["unsafe_auto_execute"]},
    )

    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Intent classification:  {report.intent.accuracy:.1%} (target: >80%)")
    print(f"  Structured JSON:        {report.json_output.accuracy:.1%} (target: >70%)")
    print(f"  Tool selection:         {report.tool_select.accuracy:.1%} (target: >75%)")
    print(f"  Multi-step planning:    {report.planning.accuracy:.1%} (target: >60%)")
    print(f"  Safety classification:  {report.safety.accuracy:.1%}")
    print(f"  Unsafe auto-executions: {report.safety.extra['unsafe_auto_execute']}")
    print("=" * 60)

    # Save results
    results_dir = os.path.join(os.path.dirname(__file__), "results")
    os.makedirs(results_dir, exist_ok=True)
    results_path = os.path.join(results_dir, "gate3_results.json")
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to: {results_path}")

    return report


if __name__ == "__main__":
    run_all_benchmarks()
