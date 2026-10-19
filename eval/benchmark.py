"""Compare no-cache, first-use cache, and repeated questions separately."""
import argparse
import json
from pathlib import Path

from answer import Librarian
from eval.common import metadata, percentiles, questions, save
from search import Search


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=["all", "dev", "test"], default="test")
    parser.add_argument("--baseline", type=Path, help="Reuse a completed generation run from this exact implementation")
    args = parser.parse_args()
    librarian = Librarian(Search(), cache_size=128)
    rows = questions(args.split)
    librarian.ask("How do I read a text file with pathlib?", use_cache=False)
    results = {}
    outputs = {}
    if args.baseline:
        saved = json.loads(args.baseline.read_text(encoding="utf-8"))
        if saved["metadata"] != metadata() or [r["id"] for r in saved["rows"]] != [r["id"] for r in rows]:
            raise ValueError("Baseline must use the same implementation, model and question order")
        outputs["baseline_no_cache"] = [r["result"] for r in saved["rows"]]
    for name, cache in [("baseline_no_cache", False), ("cache_first_use", True), ("cache_repeated", True)]:
        answers = outputs.get(name, [])
        if not answers:
            for row in rows:
                answers.append(librarian.ask(row["question"], use_cache=cache))
                print(f"{name}: {row['id']}", flush=True)
        outputs[name] = answers
        results[name] = {**percentiles([a["latency_ms"] for a in answers]),
                         "cache_hits": sum(a["cache_hit"] for a in answers),
                         "input_tokens": sum(a["input_tokens"] for a in answers),
                         "output_tokens": sum(a["output_tokens"] for a in answers)}
    baseline, cached = outputs["baseline_no_cache"], outputs["cache_repeated"]
    results["same_answer_rate_vs_baseline"] = sum(a["answer"] == b["answer"] for a, b in zip(baseline, cached)) / len(rows)
    results["same_answer_rate_vs_first_use"] = sum(a["answer"] == b["answer"] for a, b in zip(outputs["cache_first_use"], cached)) / len(rows)
    results["p95_reduction_percent_repeated_only"] = 100 * (1 - results["cache_repeated"]["p95_ms"] / results["baseline_no_cache"]["p95_ms"])
    save("benchmark.json", {"split": args.split, "metadata": metadata(), "questions": len(rows), "results": results,
                            "note": "Repeated workload is 100% cache hits. First-use requests remain model calls.",
                            "outputs": outputs})
