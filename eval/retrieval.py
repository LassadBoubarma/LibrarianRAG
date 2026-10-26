"""Measure source-passage recall, not just whether the right document appears."""
import argparse
from pathlib import Path

from eval.common import percentiles, questions, relevant, save
from search import Search
from settings import INDEX


def evaluate(search, mode, rows, k=5):
    details, times = [], []
    for row in rows:
        found, elapsed = search.retrieve(row["question"], mode=mode, k=k)
        hit = any(relevant(c, row) for c in found)
        details.append({"id": row["id"], "hit": hit, "chunks": [c["id"] for c in found]})
        times.append(elapsed)
    return {"mode": mode, "questions": len(rows), "k": k,
            "recall_at_k": sum(d["hit"] for d in details) / len(details),
            **percentiles(times), "details": details}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["keyword", "vector", "hybrid", "rerank"], default="rerank")
    parser.add_argument("--split", choices=["all", "dev", "test"], default="test")
    parser.add_argument("--index", type=Path, default=INDEX)
    args = parser.parse_args()
    engine = Search(args.index)
    rows = [r for r in questions(args.split) if r["answerable"]]
    engine.retrieve("How do I read a text file?")  # Untimed warmup.
    result = evaluate(engine, args.mode, rows)
    result["split"] = args.split
    save("retrieval.json", result)
