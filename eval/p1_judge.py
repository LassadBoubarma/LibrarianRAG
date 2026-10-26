"""Reuse Project 1's call_json function to grade saved RAG answers."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
from typing import Literal

from pydantic import BaseModel

from eval.common import RESULTS, save
from settings import OLLAMA_URL, ROOT

P1_URL = "https://github.com/BLACK2202/sql-explanation-grader.git"
P1_COMMIT = "23473e6998e69718b32ec7c8963d0cfa86a23fdb"


class RagVerdict(BaseModel):
    grade: Literal["good", "bad"]
    correct: bool
    faithful: bool
    citation_supports_claim: bool
    reason: str


def load_p1(path):
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "clone", "--quiet", P1_URL, str(path)], check=True)
        subprocess.run(["git", "-C", str(path), "checkout", "--quiet", P1_COMMIT], check=True)
    commit = subprocess.check_output(["git", "-C", str(path), "rev-parse", "HEAD"], text=True).strip()
    if commit != P1_COMMIT:
        raise ValueError(f"Expected P1 commit {P1_COMMIT}; got {commit}. Use a separate pinned checkout.")
    os.environ["OLLAMA_HOST"] = OLLAMA_URL
    spec = importlib.util.spec_from_file_location("p1_llm", path / "harness" / "llm.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.call_json


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--p1", type=Path, default=ROOT / "work" / "p1")
    parser.add_argument("--judge-model", default="qwen2.5:7b")
    parser.add_argument("--input", type=Path, default=RESULTS / "generation.json")
    args = parser.parse_args()
    call_json = load_p1(args.p1.resolve())
    prompt = (ROOT / "eval" / "judge_prompt.md").read_text(encoding="utf-8")
    source = args.input.read_bytes()
    run_hash = hashlib.sha256(source + prompt.encode() + args.judge_model.encode() + P1_COMMIT.encode()).hexdigest()[:12]
    checkpoint = RESULTS / f"judge-{run_hash}.jsonl"
    completed = {}
    if checkpoint.exists():
        completed = {r["id"]: r for r in map(json.loads, checkpoint.read_text(encoding="utf-8").splitlines()) if r.get("error") is None}
    rows = json.loads(source)["rows"]
    if len(rows) != 112 or len({r["id"] for r in rows}) != len(rows):
        raise ValueError("Expected 112 distinct answers in the current full-set file")
    RESULTS.mkdir(parents=True, exist_ok=True)
    with checkpoint.open("a", encoding="utf-8") as file:
        for row in rows:
            if row["id"] in completed:
                continue
            payload = {"question": row["question"], "expected_answer": row["answer"],
                       "answerable": row["answerable"], "reference_passage": row["source_passage"],
                       "actual_answer": row["result"]["answer"], "abstained": row["result"]["abstained"],
                       "cited_quotes": [c["quote"] for c in row["result"]["sources"]],
                       "cited_passages": [c["text"] for c in row["result"]["sources"]]}
            try:
                verdict, metrics = call_json(args.judge_model, prompt, json.dumps(payload), RagVerdict, seed=42)
                # Refusal labels are known from the dataset; a judge cannot reverse them.
                raw_verdict = verdict.model_dump()
                if row["result"]["abstained"]:
                    verdict.correct = not row["answerable"]
                    verdict.faithful = False
                    verdict.citation_supports_claim = False
                    verdict.grade = "good" if verdict.correct else "bad"
                result = {"id": row["id"], "input": row["question"], "output": row["result"]["answer"],
                          "score": int(verdict.correct), "reason": verdict.reason,
                          "verdict": verdict.model_dump(), "raw_verdict": raw_verdict,
                          "refusal_rule_applied": row["result"]["abstained"], "judge_cost": metrics, "error": None}
            except Exception as error:
                result = {"id": row["id"], "score": 0, "error": str(error)}
            completed[row["id"]] = result
            file.write(json.dumps(result) + "\n")
            file.flush()
            print(f"{row['id']}: {result.get('reason', result.get('error'))}", flush=True)
    ordered = [completed[r["id"]] for r in rows]
    answered = [completed[r["id"]] for r in rows if not r["result"]["abstained"]]
    errors = sum(r.get("error") is not None for r in ordered)
    if errors:
        print(f"WARNING: {errors} grader calls failed; do not report incomplete scores as full-set grades.")
    summary = {"questions": len(rows), "judge_model": args.judge_model, "p1_commit": P1_COMMIT,
               "errors": errors,
               "model_judged_correctness": (sum(r["score"] for r in ordered) / len(rows)) if not errors else None,
               "model_judged_faithfulness_answered": (sum(r.get("verdict", {}).get("faithful", False) for r in answered) / len(answered)) if answered and not errors else None,
               "model_judged_citation_support_answered": (sum(r.get("verdict", {}).get("citation_supports_claim", False) for r in answered) / len(answered)) if answered and not errors else None,
               "note": "Model judgments, not human labels. Review the individual reasons and quotes."}
    save("p1_judge.json", {"generation_sha256": hashlib.sha256(source).hexdigest(),
                           "summary": summary, "rows": ordered})
