# LibrarianRAG - Project 2 report

CS496 | 26 October 2026

## 1. Corpus and users

This is a question-answering helper for students who consult the Python standard-library documentation. The corpus is 25 official Python 3.14.0 pages, containing 209,222 extracted words (about 418 equivalent pages at 500 words per page, not an actual PDF page count). The cleaned documents, original links, anchors and license are included in the repository.

There are 102 drafted, source-linked answerable questions and 10 out-of-scope questions. These are engineering test questions, not questions collected from real users. Students are the intended users, but instructor approval and anonymous classmate feedback are still pending.

## 2. Pipeline

The offline code extracts named sections, keeps each source URL, splits text into 180-token chunks with no overlap and embeds them with all-MiniLM-L6-v2. The shipped index data is 3,297 chunks. A NumPy matrix and JSON metadata are sufficient at this size; a separate vector database would add setup work.

For each question BM25 and vector search collect 30 results apiece. Reciprocal rank fusion combines the lists, a MiniLM cross-encoder reranks 20 candidates, and the five best passages go to Qwen 2.5 3B through Ollama. A document selector filters results. The app does not rewrite follow-up questions.

The model returns an answer and a passage number. The server copies the passage from its index instead of accepting a model-written quote. It refuses low-relevance or invalid-source answers. A copied quote is not proof that the claim follows from that quote. Recent small code fixes tighten input handling, refusals and named-API citations but have not yet been reevaluated.

## 3. Retrieval results

Saved 19 October 2026 ablation on all 102 answerable questions. A hit requires the annotated evidence span in the top five, not just a matching page. Times are local search-step milliseconds.

| Search | Recall@5 | p50 search | p95 search |
| --- | --- | --- | --- |
| keyword | 73.5% | 5.6 ms | 9.5 ms |
| vector | 63.7% | 12.2 ms | 15.9 ms |
| hybrid | 84.3% | 19.8 ms | 25.5 ms |
| rerank | 91.2% | 671.3 ms | 820.2 ms |

Reranking improves recall from hybrid 84.3% to 91.2%, at a large search-latency cost. This is a descriptive test set; 20 questions were used in development and the final set was not kept sealed.

## 4. Generation and checking

Saved 19 October 2026 run of 112 questions (the answer-generating code has since changed):

| Measure | Saved result |
| --- | --- |
| Answer coverage, 102 answerable | 93.1% |
| Refusal, 10 out-of-scope | 100.0% |
| Gold-evidence citation, 102 answerable | 65.7% |
| Copied quote exists, answered responses | 100.0% |
| Token overlap F1, not semantic correctness | 0.314 |
| End-to-end p50, saved run | 3261.9 ms |
| End-to-end p95, saved run | 3583.3 ms |
| P1 correctness / faithfulness, all 112 | not measured |

There were 95 answered items in the saved run: 95 of 102 answerable questions were answered and all 10 out-of-scope questions were refused. A 100% copied-quote rate does not establish faithfulness; the gold passage was cited on only 65.7% of answerable questions. The token F1 of 0.314 measures overlap of words, not answer quality.

The full Project 1 correctness/faithfulness/citation judging on all 112 current saved answers has not been run. The only existing five-question judge file belongs to a different development version and is excluded. Human grading columns remain blank. Examples of actual wrong answers appear in quality_review.md; no model-judge percentages are invented.

## 5. Week 8 and cost

The cache holds 128 exact-question responses. No 50% p95 reduction has been demonstrated by a completed benchmark.

Cache first-use and repeat p50/p95: **not measured**. `benchmark.json` does not exist.

A chunking trial on 20 development questions gave recall@5 85% at 120/24, and 90% at both 180/0 and 180/36. The chosen 180/0 index is smaller, but this does not prove the assigned 50% end-to-end optimisation target.

Local inference incurs no external per-token API fee, but machines, electricity and hosting cost money. For a purely hypothetical fixed $20/month host: 1,000 requests cost $0.020/request, and 100,000 cost $0.00020/request only if capacity is sufficient. This is a cost illustration, not a host quote or load measurement. The app permits one active model call and returns HTTP 503 for simultaneous requests.

## 6. Failures and remaining work

Observed mistakes include saying that all([]) returns a start value, naming zip() instead of itertools.chain, mixing up csv.writer and DictWriter, and giving the wrong sorted insertion function. Long code blocks, flattened tables, cross-references and ambiguous names remain difficult. Some questions are refused despite having an answer; some cited passages do not support the actual claim.

The project has a local browser preview and nine earlier automated checks recorded in its notes. In this environment, offline data integrity checks and four new tests passed; the full dependency-based test suite and updated model run are not verified. No public URL, instructor approval, classmate study or human grades are available.

Documentation and code were prepared with coding-assistant support. The owner should read explain.md, review the code and actual scores, obtain approval and genuine user feedback, and complete the live judge, benchmark and deployment before claiming those requirements are met.
