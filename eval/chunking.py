"""Test chunk sizes on development questions only; leave the test set alone."""
import subprocess
import sys

from eval.common import questions, save
from eval.retrieval import evaluate
from search import Search
from settings import ROOT


if __name__ == "__main__":
    results = []
    rows = [q for q in questions("dev") if q["answerable"]]
    for size, overlap in [(120, 24), (180, 0), (180, 36)]:
        index = ROOT / "work" / f"index-{size}-{overlap}"
        subprocess.run([sys.executable, "build_index.py", "--size", str(size), "--overlap", str(overlap), "--output", str(index)], check=True)
        search = Search(index)
        search.retrieve("How do I read a file?")
        result = evaluate(search, "rerank", rows)
        results.append({"size": size, "overlap": overlap, "chunks": len(search.chunks), "split": "dev", **result})
        del search
    save("chunking.json", results)
