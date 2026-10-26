# LibrarianRAG

A small question-answering app for the Python documentation. Ask a question, get a short answer, and open the passage it came from.

The project uses an open-source project's documentation, one of the CS496 Project 2 ideas. Python is useful to students, the sources are public, and the answers can be checked. The corpus is 25 long reference documents from Python 3.14.0, about 209,000 words in total.

## Run it

You need Python 3.11 or 3.12, Git, and [Ollama](https://ollama.com) installed and running. The first setup downloads Python packages and models, so allow several GB of disk space. No paid API key is needed.

After cloning this repository, run this one setup command:

```sh
python setup_project.py
```

On Windows with several Python versions installed, use `py -3.11 setup_project.py` instead.

Then run:

```sh
python run.py
```

Open [localhost:8000](http://127.0.0.1:8000). Try:

- How do I read a file as text with pathlib?
- Does random.sample use replacement?
- What is my university Wi-Fi password?

The last question should return “I don't know.”

## How it works

`Documents -> chunks -> keyword + vector search -> reranker -> answer with source`

BM25 finds matching words. MiniLM finds similar meaning. A cross-encoder ranks the best candidates again. Qwen 2.5 3B reads the top five passages and answers. The server copies the cited passage from the index, so the model does not write its own evidence. Repeated questions use a small memory cache.

The code is ordinary Python functions and two small classes. There is no LangChain or database server. [explain.md](explain.md) walks through the files and gives a short demo plan.

## Results

These are saved results from 19 October 2026, Windows 3.11, Ryzen 5 5600X, RTX 3060. The saved answers were produced before the latest code fixes; rerun generation for updated scores. The development questions are included; this is not a blind test.

| Search | Recall@5 | p50 search | p95 search |
| --- | --- | --- | --- |
| keyword | 73.5% | 5.6 ms | 9.5 ms |
| vector | 63.7% | 12.2 ms | 15.9 ms |
| hybrid | 84.3% | 19.8 ms | 25.5 ms |
| rerank | 91.2% | 671.3 ms | 820.2 ms |

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

**Correctness and faithfulness need the full Project 1 judge and human review.** Quote existence (100%) only means the evidence text was copied from a document. It does not show that the answer is correct. See [quality_review.md](quality_review.md) for concrete mistakes.

**Cache benchmark:** No 50% p95 reduction has been demonstrated by a completed benchmark. The benchmark is resumable and must be run with Ollama available.

## Evaluation

```sh
python run.py -m unittest discover -s tests -v
python run.py -m eval.ablation --split all
python run.py -m eval.generation --split all
python run.py -m eval.benchmark --split all --baseline eval/results/generation.json
ollama pull qwen2.5:7b
python run.py -m eval.p1_judge
```

There are 102 drafted questions with answers and real source passages, plus 10 unanswerable questions. Twenty questions are marked for development. The final full-set results are descriptive; this is not a sealed, independently collected benchmark.

The last command reuses `call_json` from [our Project 1 grader](https://github.com/BLACK2202/sql-explanation-grader), pinned to commit `23473e6`. Its SQL rubric is replaced with a RAG rubric. Correctness, faithfulness and citation support are reported separately. Those scores come from a model judge; they are not human grades. See [eval/README.md](eval/README.md).

## Project files

| File | Purpose |
| --- | --- |
| `corpus.py`, `build_index.py` | Prepare the documents and index. |
| `search.py`, `answer.py` | Retrieve passages and answer questions. |
| `app.py`, `templates/index.html` | The web form and JSON API. |
| `data/` | Source snapshot, questions, licenses and blank feedback form. |
| `eval/` | Retrieval, generation, ablation and speed checks. |
| `design.md` | Design choices and known limits. |
| `optimisation.md` | Measured before/after comparison and cost model. |
| `report.md`, `report.pdf` | Short project report. |
| `postmortem.md` | Problems found during implementation. |
| `quality_review.md` | Concrete mistakes in the saved answers. |
| `verify_saved.py` | Model-free integrity check for saved data. |

## Deployment and remaining work

The app has been tested locally. **A public deployment URL is not available yet.** [deployment.md](deployment.md) explains how to run it on a server. GitHub Pages cannot host this Python service.

Before submitting: get the instructor's approval for the corpus, collect real classmate feedback, review the question set and model grades, and add the actual live URL. No approval, user feedback or human grades have been invented.

## Contributions

Project owner: Lassad Boubarma. The implementation and draft documentation were prepared with coding-assistant support. The Project 1 model-calling code comes from the linked SQL Explanation Grader. Review the code and update this section with the team's actual contributions before submission.

The source text belongs to the Python documentation contributors. Its license and the text-processing changes are described in [data/README.md](data/README.md).
