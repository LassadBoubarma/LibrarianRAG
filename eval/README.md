# Evaluation

From the repository root:

```sh
python run.py -m unittest discover -s tests -v
python run.py -m eval.ablation
python run.py -m eval.generation
python run.py -m eval.benchmark
python run.py -m eval.chunking
```

Ollama must be running for generation and benchmarking. The first model load is excluded by an untimed warmup. Requests are sequential; these are local pipeline timings, not network load tests. Keep other model jobs idle when comparing times.

`retrieval.py` measures one search mode. `ablation.py` compares keyword, vector, hybrid and hybrid plus reranking on the same test questions. A hit requires the actual evidence span, not merely the correct document title.

`generation.py` saves every answer and quote. Token F1 measures word overlap with the expected answer. Gold citation rate checks the annotated passage. Exact quote rate checks that a quoted string exists. None of those is a substitute for semantic correctness or faithfulness.

Fill the empty grading columns in `results/human_review.csv` with 0 or 1. Correctness means the answer actually answers the question. Faithfulness means every claim follows from the cited text. Citation support means the cited passage justifies the claim, not merely that the URL opens. Keep abstentions on answerable questions in the denominator for correctness. Do not grade a refusal as a supported factual answer.

The assignment mentions a Project 1 harness. No P1 harness was supplied, so these scripts run independently. `questions.jsonl` and the generated answer records can be used as inputs to that harness later.

`benchmark.py` reports three workloads separately: no cache, empty cache, and repeated questions already in the cache. The repeat test is a deliberate 100% hit scenario, not an estimate of real traffic. It also compares answer text. It does not claim a measured human accuracy change.

`chunking.py` tests size and overlap on the development split. It stores temporary indexes under ignored `work/`.
