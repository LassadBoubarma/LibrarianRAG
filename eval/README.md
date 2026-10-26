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

Project 1 integration: run `python run.py -m eval.p1_judge` after generation. This downloads a pinned checkout of [the Project 1 grader](https://github.com/BLACK2202/sql-explanation-grader) and imports its actual `harness/llm.py` function. Install the judge with `ollama pull qwen2.5:7b` first. The RAG prompt replaces the SQL rubric. Results retain the P1 score, reason and judge-cost fields, plus separate correctness, faithfulness and citation judgments. The checkpoint hash includes the answers, prompt, judge model and P1 commit, so a changed run cannot silently reuse old grades.

The default generator and judge both use Qwen 2.5 7B. Shared model biases can inflate these scores. Review a sample manually or use another judge with `--judge-model` before relying on the grades. The adapter preserves raw verdicts and applies known refusal labels directly when the model contradicts them.

`benchmark.py` reports three workloads separately: no cache, empty cache, and repeated questions already in the cache. The repeat test is a deliberate 100% hit scenario, not an estimate of real traffic. It also compares answer text. It does not claim a measured human accuracy change.

After the benchmark and full P1 grading, run `python run.py -m eval.cache_accuracy`. It reuses grades when the answer and cited evidence are identical, and calls the P1 judge for changed outputs. This measures the model-judged accuracy change between the independent no-cache and cached runs.

`chunking.py` tests size and overlap on the development split. It stores temporary indexes under ignored `work/`.
