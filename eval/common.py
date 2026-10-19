import json
import hashlib
import platform
from pathlib import Path

import numpy as np

from settings import CHAT_MODEL, DATA, ROOT

RESULTS = ROOT / "eval" / "results"


def metadata():
    paths = [ROOT / name for name in ["answer.py", "search.py", "settings.py", "index/config.json", "data/questions.jsonl"]]
    return {"model": CHAT_MODEL, "python": platform.python_version(), "platform": platform.system(),
            "implementation_sha256": hashlib.sha256(b"".join(p.read_bytes() for p in paths)).hexdigest()}


def questions(split="all"):
    rows = [json.loads(line) for line in (DATA / "questions.jsonl").read_text(encoding="utf-8").splitlines()]
    return [r for r in rows if split == "all" or r["split"] == split]


def relevant(chunk, question):
    return (chunk["source_id"] == question["source_id"]
            and chunk["start"] <= question["evidence_start"]
            and chunk["end"] >= question["evidence_end"])


def percentiles(values):
    return {"p50_ms": round(float(np.percentile(values, 50)), 3),
            "p95_ms": round(float(np.percentile(values, 95)), 3)}


def save(name, data):
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / name).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved eval/results/{name}", flush=True)
