"""Make overlapping token chunks and save their embeddings in two plain files."""
import argparse
import hashlib
import json

import numpy as np
import torch
from sentence_transformers import SentenceTransformer

from settings import DATA, EMBED_MODEL, INDEX


def make_chunks(records, tokenizer, size=180, overlap=0):
    if not 1 <= size <= 240:
        raise ValueError("Use 1 to 240 tokens so the embedding model can read the whole chunk")
    if not 0 <= overlap < size:
        raise ValueError("Overlap must be smaller than chunk size")
    chunks = []
    for record in records:
        offsets = tokenizer(record["text"], add_special_tokens=False, return_offsets_mapping=True, verbose=False)["offset_mapping"]
        for start in range(0, len(offsets), size - overlap):
            end = min(start + size, len(offsets))
            a, b = offsets[start][0], offsets[end - 1][1]
            chunks.append({**record, "source_id": record["id"],
                           "id": f"{record['id']}:{start}", "start": a, "end": b,
                           "text": record["text"][a:b]})
            if end == len(offsets):
                break
    return chunks


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--size", type=int, default=180)
    parser.add_argument("--overlap", type=int, default=0)
    parser.add_argument("--output", type=str, default=str(INDEX))
    args = parser.parse_args()
    from pathlib import Path
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    torch.set_num_threads(4)
    model = SentenceTransformer(EMBED_MODEL, device="cpu")
    records = [json.loads(line) for line in (DATA / "documents.jsonl").read_text(encoding="utf-8").splitlines()]
    chunks = make_chunks(records, model.tokenizer, args.size, args.overlap)
    # Chunk text alone fits the embedding model's 256-token input limit.
    vectors = model.encode([c["text"] for c in chunks], normalize_embeddings=True,
                           batch_size=64, show_progress_bar=True)
    np.save(output / "vectors.npy", vectors)
    (output / "chunks.json").write_text(json.dumps(chunks, ensure_ascii=False), encoding="utf-8")
    (output / "config.json").write_text(json.dumps({
        "model": EMBED_MODEL, "size": args.size, "overlap": args.overlap,
        "chunks": len(chunks),
        "corpus_sha256": hashlib.sha256((DATA / "documents.jsonl").read_bytes()).hexdigest(),
    }, indent=2), encoding="utf-8")
    print(f"Saved {len(chunks)} chunks in {output}")


if __name__ == "__main__":
    main()
