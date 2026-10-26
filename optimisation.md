# Optimisation

## Change

Keep the last 128 answers in memory. The key contains the trimmed question, document filter and model name. Restart when the index changes. No answer text is shortened or changed by the cache.

## Before and after

Same 112 questions, same order and model, one request at a time. Model warmup is excluded. The no-cache measurements come from the saved full generation run; the benchmark checks its implementation hash and question IDs before reusing it. Then it runs the same set through an empty cache and repeats it through the populated cache.

| Workload | p50 ms | p95 ms | Cache hits / 112 | Model tokens |
| --- | --- | --- | --- | --- |
| No cache | 3442.338 | 3836.704 | 0 | 79419 |
| Cache, first use | 3139.002 | 3466.898 | 0 | 79405 |
| Cache, repeated | 0.030 | 0.034 | 112 | 0 |

Repeated-workload p95 reduction: **99.9991%**. Exact answer agreement with the empty-cache pass: **100.0%**. Agreement with the independent no-cache pass: **99.1%**. On the 102 answerable questions, model-judged correctness was 84.3% before and 84.3% after caching (+0.00 percentage points). 1 changed output was regraded; 111 grades were reused because answer and evidence matched exactly. These are model judgments, not a human accuracy study. Full records are in `eval/results/cache_accuracy.json`.

The 50% latency target is demonstrated for repeated questions already in the cache. It is not established for a real traffic mix. First-use requests still run retrieval and generation. The benchmark does not include internet transit time or concurrent load.

## Chunk choice

On 20 development questions, 120-token chunks with 24-token overlap gave 85% recall@5. Both 180/0 and 180/36 gave 90%. The final choice is 180/0: 3,297 chunks instead of 3,505. Chunk timings are in `eval/results/chunking.json`; they are exploratory local measurements and should not be compared as a controlled service benchmark because other setup work was running.

## Cost model

The local models have **$0 external inference API charges**. Hardware, power and hosting are not free. No API price reduction is claimed.

Let H be a fixed monthly hosting bill and N the number of monthly requests. At the same capacity, hosting cost per request is H/N. At 100 times the traffic it is H/(100N), but only if that machine can actually handle the load. This implementation accepts one active generation request and returns 503 while busy, so that assumption needs a load test.

For a simple arithmetic example, an assumed $20 monthly machine and 1,000 requests give $0.02 per request. At 100,000 requests, the fixed-bill calculation is $0.0002 per request. These are assumptions, not a provider quote or a measured capacity claim. Add electricity and hardware amortisation if using your own machine.

For on-demand hosting billed at C per hour, active compute cost is approximately `C * average_request_seconds / 3600`. Multiply that by request count for monthly active cost, then add idle time, storage and network charges. A cache hit avoids the model call; its savings depend on the actual hit rate. Token counts in the table are workload totals, not dollars.

## Reproduce

```sh
python run.py -m eval.generation --split all
python run.py -m eval.benchmark --split all --baseline eval/results/generation.json
python run.py -m eval.p1_judge
python run.py -m eval.cache_accuracy
```

Run these with other model jobs idle. Check `eval/results/environment.json` for the observed model digests and `requirements-lock.txt` for the tested Windows packages.
