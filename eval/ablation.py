"""Compare four retrieval methods on exactly the same questions."""
import argparse

from eval.common import questions, save
from eval.retrieval import evaluate
from search import Search


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=["all", "dev", "test"], default="test")
    args = parser.parse_args()
    engine = Search()
    engine.retrieve("How do I read a text file?")
    rows = [r for r in questions(args.split) if r["answerable"]]
    results = []
    for mode in ["keyword", "vector", "hybrid", "rerank"]:
        result = evaluate(engine, mode, rows)
        result["split"] = args.split
        results.append(result)
        print(f"{mode}: recall@5={result['recall_at_k']:.3f}", flush=True)
    save("ablation.json", results)
