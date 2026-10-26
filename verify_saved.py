"""Offline integrity checks for the included evaluation data (no model required)."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parent

def read_lines(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]

def main():
    documents = {r["id"]: r for r in read_lines(root / "data/documents.jsonl")}
    questions = read_lines(root / "data/questions.jsonl")
    generations = json.loads((root / "eval/results/generation.json").read_text(encoding="utf-8"))
    ablations = json.loads((root / "eval/results/ablation.json").read_text(encoding="utf-8"))
    if (root / "index/chunks.json").exists():
        index = json.loads((root / "index/chunks.json").read_text(encoding="utf-8"))
        config = json.loads((root / "index/config.json").read_text(encoding="utf-8"))
        assert config["corpus_sha256"] == hashlib.sha256((root / "data/documents.jsonl").read_bytes()).hexdigest()
        assert len(index) == config["chunks"] == 3297
    else:
        print("INDEX: not included in clean clone; setup_project.py rebuilds it")
    assert len(questions) == len(generations["rows"]) == 112
    assert len({q["id"] for q in questions}) == 112
    assert sum(q["answerable"] for q in questions) == 102
    assert [q["id"] for q in questions] == [r["id"] for r in generations["rows"]]
    for q in questions:
        if q["answerable"]:
            doc = documents[q["source_id"]]["text"]
            assert q["source_passage"] in doc, q["id"]
            assert doc[q["evidence_start"]:q["evidence_end"]], q["id"]
    for row in generations["rows"]:
        for source in row["result"]["sources"]:
            assert source["quote"] == source["text"], row["id"]
    for a in ablations:
        assert a["questions"] == 102 and len(a["details"]) == 102
        assert abs(a["recall_at_k"] - sum(d["hit"] for d in a["details"]) / 102) < 1e-10
    summary = generations["summary"]
    assert summary["human_correctness"] is None and summary["human_faithfulness"] is None
    if (root / "eval/results/benchmark.json").exists():
        print("BENCHMARK: present; verify its source metadata before treating it as complete")
    print("PASS: 112 saved answers, 102 source-linked questions, 10 out-of-scope questions")
    print("PASS: source quotations, corpus hash, answer IDs, saved ablation arithmetic")
    print("NOT RUN: Ollama generation, current P1 judge, cache timing, clean-machine setup or hosting")

if __name__ == "__main__":
    main()
