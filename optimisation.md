# Optimisation

## What changed

The service stores up to 128 question answers in a small in-memory cache. A hit avoids retrieval, reranking and the Ollama call. The cache key includes the exact question, selected document and model. Restart the server when changing documents or model versions. The app is otherwise a simple, single-worker generator.

## Before and after

The complete generation run on 19 October 2026, Windows 3.11, Ryzen 5 5600X, RTX 3060 measured **p50 3261.9 ms** and **p95 3583.3 ms** without cached responses. It contains 112 sequential questions. The cache benchmark was interrupted before completion. No completed paired before/after latency comparison is supplied.

Cache first-use and repeat p50/p95: **not measured**. `benchmark.json` does not exist.

No 50% p95 reduction has been demonstrated by a completed benchmark. A full cache has no effect on first-time questions. Even after completing the benchmark, the all-repeat result must not be presented as the expected speedup for normal traffic. A real cache-hit percentage and mixed workload would need to be measured with users.

The code now saves `eval/results/benchmark_progress.json` after each question, so an interrupted benchmark can resume without losing the completed calls. The progress file is temporary and is not a result.

## Smaller index

On 20 development questions, reranked recall@5 was **85%** with 120 tokens/24 overlap, **90%** with 180/0 and **90%** with 180/36. The selected 180/0 index has 3,297 chunks, compared with 3,505 for 180/36. This is an index-size choice, not a demonstrated 50% latency reduction. Timings in `chunking.json` were exploratory, not controlled service timings.

## Cost per request and 100x

There is **no external inference API fee** because the models run on Ollama. Computer time, hardware, electricity, bandwidth and hosting still cost money. With an assumed fixed monthly hosting bill H and N requests, the simple per-request hosting figure is H/N. For a hypothetical $20/month and 1,000 monthly requests, that is $0.020/request; at 100,000 it is $0.00020/request **only if the same machine has enough capacity**. Neither $20 nor that capacity has been observed or quoted from a provider.

At an hourly active compute price C, active compute cost for one request is roughly `C * (request seconds / 3600)`, plus idle time and other charges. The app serialises model calls and returns 503 when busy. It has not been load-tested at 100x; do not assume the fixed-cost example can be achieved.

## Complete the benchmark locally

Run after installing Python 3.11/3.12, dependencies and Ollama. Keep other GPU work idle. The new code must be used for **both** the baseline and the repeated run:

```sh
python run.py -m eval.generation --split all
python run.py -m eval.benchmark --split all --baseline eval/results/generation.json
python .venv/bin/python continuation/make_deliverables.py
```

On Windows replace the last command with `.venv\Scripts\python continuation/make_deliverables.py`. Save the resulting `benchmark.json` and check its environment metadata. If the run stops, repeat the benchmark command. The benchmark uses all 112 questions, one request at a time, and separates no-cache, empty-cache and already-cached requests. It does not measure external network time or concurrent users.
