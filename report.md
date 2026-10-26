# LibrarianRAG - Project 2 report

CS496 | 26 October 2026

## 1. Corpus and users

The project is a question-answering helper for students reading Python documentation. It uses 25 official Python 3.14.0 reference documents: 209,222 words, about 418 pages at 500 words per page. This is an estimated page count. The cleaned snapshot and source hashes are committed.

The documents are public and covered by the included Python license. No student records are included. The intended users are classmates learning Python; real user feedback and instructor approval have not yet been collected. data/feedback.csv is deliberately blank.

## 2. Pipeline design

Offline: extract sections and source anchors, split into 180-token chunks, embed with all-MiniLM-L6-v2, and save JSON plus a NumPy matrix. There are 3,297 chunks. A flat index fits in memory and avoids a database service.

Online: BM25 and vector search each return 30 candidates. Reciprocal rank fusion combines them. A MiniLM cross-encoder reranks the best 20, and Qwen 2.5 7B answers from the best five. A document filter is applied before ranking. Questions are not rewritten.

The model chooses a source number. The app copies the cited passage from the index and links to the original documentation. Missing sources, explicit refusals and low relevance scores return an unknown response. A copied passage may still be interpreted incorrectly.

Chunk-size trial on 20 development questions: 120/24 gave 85% recall@5; 180/0 and 180/36 both gave 90%. The smaller 180/0 index was selected. Long code blocks can still cross chunk boundaries.

## 3. Retrieval results

The full set contains 102 drafted answerable questions and 10 out-of-scope questions. Retrieval uses only the 102 answerable items. A hit requires the annotated evidence span from the correct source section among the top five chunks, not just a matching document title.

| Search | Recall@5 | Search p95 |
| --- | --- | --- |
| keyword | 73.5% | 11.9 ms |
| vector | 63.7% | 17.2 ms |
| hybrid | 84.3% | 25.6 ms |
| rerank | 91.2% | 794.0 ms |

These are descriptive engineering results, not a sealed holdout. Twenty questions were used for development, and preliminary test results were viewed during implementation. Questions are mostly short API lookups; real student questions may be harder.

## 4. Generation and Project 1

| Measure | Result |
| --- | --- |
| Model-judged correctness (102 answerable) | 87.3% |
| Model-judged correctness (all 112) | 88.4% |
| Model-judged faithfulness (answered only) | 93.9% |
| Model-judged citation support (answered only) | 92.9% |
| Answer coverage (102 answerable) | 97.1% |
| Correct refusal (10 out-of-scope) | 100.0% |
| Gold-passage citation rate (102 answerable) | 79.4% |
| Answer token F1 (word-overlap proxy) | 0.532 |

The adapter imports the actual call_json function from BLACK2202/sql-explanation-grader at commit 23473e6. It replaces the SQL rubric with question correctness, support from cited passages and citation relevance. Qwen 2.5 7B judges the saved answers. Raw verdicts and reasons are retained. Known refusal labels override contradictory model judgments.

Model grades are not human labels. Generator and judge use the same model, so shared biases can inflate scores. Token F1 is only word overlap. Exact quote existence is guaranteed by copying evidence and is not a faithfulness result. The human review CSV has empty grading columns and must be reviewed before final submission.

## 5. Optimisation and cost

| Workload | p50 ms | p95 ms | Cache hits / 112 | Model tokens |
| --- | --- | --- | --- | --- |
| No cache | 3317.391 | 3810.670 | 0 | 79272 |
| Cache, first use | 3228.638 | 3676.689 | 0 | 79271 |
| Cache, repeated | 0.023 | 0.038 | 112 | 0 |

The 128-entry cache reduced repeated-workload p95 by 99.9990%. Exact cached/first-use answer agreement was 100.0%; agreement with the separate no-cache run was 94.6%. Identical stored answers preserve their grading. The 50% target is demonstrated for a 100% repeat workload, not for unseen questions or an unknown real hit rate.

On the 102 answerable questions, model-judged correctness was 87.3% before and 87.3% after caching (+0.00 percentage points). 7 changed outputs were regraded; 105 grades were reused because answer and evidence matched exactly.

External inference API charges are $0 because inference is local. Hosting, hardware and electricity still cost money. Fixed monthly hosting cost per request is H/N. At 100x traffic it is H/(100N) only if capacity suffices. An assumed $20/month at 1,000 requests is $0.02/request; at 100,000 it is $0.0002/request before capacity upgrades. These are illustrative assumptions, not provider prices.

## 6. Limits and remaining work

Known failures include flattened tables, split code blocks, missed cross-references, nearby APIs outranking the right API, unnecessary refusals and a model misreading real evidence. The postmortem records parsing errors, quote-generation failures and a contradictory judge result found during implementation.

The app was checked in a browser and has nine automated checks. It runs locally; a public deployment URL has not been provisioned. Deployment instructions are included. Instructor approval, real classmate feedback and human review remain outstanding and are not represented as complete.

The code and draft documentation were prepared with coding-assistant support. The project owner needs to review the implementation and understand it before presenting. explain.md provides a file-by-file reading order and demonstration plan.
