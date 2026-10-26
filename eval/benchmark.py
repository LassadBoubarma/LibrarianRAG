"""Measure no-cache, first-use and repeated requests on the same 112 questions.

If interrupted, rerun the command to resume from benchmark_progress.json.
"""
import argparse
import json
from collections import OrderedDict
from copy import deepcopy
from pathlib import Path

from answer import Librarian
from eval.common import RESULTS, metadata, percentiles, questions, save
from search import Search
from settings import CHAT_MODEL


def answer_values(records):
    return [r["answer"] for r in records]


def measure(records):
    return {**percentiles([r["latency_ms"] for r in records]),
            "cache_hits": sum(r["cache_hit"] for r in records),
            "input_tokens": sum(r["input_tokens"] for r in records),
            "output_tokens": sum(r["output_tokens"] for r in records)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=["all", "dev", "test"], default="all")
    parser.add_argument("--baseline", type=Path, help="Saved generation.json from this exact code and machine")
    args = parser.parse_args()

    rows = questions(args.split)
    ids = [r["id"] for r in rows]
    meta = metadata()
    progress = RESULTS / "benchmark_progress.json"
    outputs = {name: [] for name in ("baseline_no_cache", "cache_first_use", "cache_repeated")}
    if progress.exists():
        state = json.loads(progress.read_text(encoding="utf-8"))
        if (state["metadata"], state["ids"]) != (meta, ids):
            raise ValueError("Stale benchmark progress. Rename benchmark_progress.json before starting a new run.")
        outputs = state["outputs"]
    if args.baseline and not outputs["baseline_no_cache"]:
        saved = json.loads(args.baseline.read_text(encoding="utf-8"))
        if saved["metadata"] != meta or [r["id"] for r in saved["rows"]] != ids:
            raise ValueError("Baseline must have the same implementation, Python, OS, model and question order. Regenerate generation.json first.")
        outputs["baseline_no_cache"] = [r["result"] for r in saved["rows"]]

    librarian = Librarian(Search(), cache_size=max(128, len(rows)))
    librarian.ask("How do I read a text file with pathlib?", use_cache=False)  # Model warmup

    def checkpoint():
        save("benchmark_progress.json", {"metadata": meta, "ids": ids, "outputs": outputs})

    for name, use_cache in (("baseline_no_cache", False), ("cache_first_use", True), ("cache_repeated", True)):
        if name == "cache_repeated":
            # After a resumed run, restore the same populated cache without extra model calls.
            for q, result in zip(rows, outputs["cache_first_use"]):
                librarian.cache[(q["question"].strip(), None, CHAT_MODEL)] = deepcopy(result)
            assert len(outputs["cache_first_use"]) == len(rows), "Complete first-use stage before repeated stage"
        for q in rows[len(outputs[name]):]:
            answer = librarian.ask(q["question"], use_cache=use_cache)
            if use_cache and (answer["cache_hit"] != (name == "cache_repeated")):
                raise RuntimeError("Unexpected cache hit; check for repeated questions")
            outputs[name].append(answer)
            checkpoint()
            print(f"{name}: {q['id']}", flush=True)
        if name == "cache_first_use" and len(outputs[name]) == len(rows):
            # If first-use stage came entirely from a checkpoint, restore it for next stage.
            librarian.cache = OrderedDict(( (q["question"].strip(), None, CHAT_MODEL), deepcopy(a))
                                          for q, a in zip(rows, outputs[name]))

    results = {name: measure(records) for name, records in outputs.items()}
    baseline, first, repeated = (outputs[name] for name in outputs)
    results["same_answer_rate_vs_baseline"] = sum(a == b for a, b in zip(answer_values(baseline), answer_values(repeated))) / len(rows)
    results["same_answer_rate_vs_first_use"] = sum(a == b for a, b in zip(answer_values(first), answer_values(repeated))) / len(rows)
    results["p95_reduction_percent_repeated_only"] = 100 * (1 - results["cache_repeated"]["p95_ms"] / results["baseline_no_cache"]["p95_ms"])
    save("benchmark.json", {"split": args.split, "metadata": meta, "questions": len(rows), "results": results,
                            "note": "Repeated requests are 100% hits; no claim about real-world hit rates or 100x capacity.",
                            "outputs": outputs})
    progress.unlink(missing_ok=True)
