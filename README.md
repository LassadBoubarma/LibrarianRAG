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

BM25 finds matching words. MiniLM finds similar meaning. A cross-encoder ranks the best candidates again. Qwen 2.5 7B reads the top five passages and answers. The server copies the cited passage from the index, so the model does not write its own evidence. Repeated questions use a small memory cache.

The code is ordinary Python functions and two small classes. There is no LangChain or database server. [explain.md](explain.md) walks through the files and gives a short demo plan.

## Results

The measured tables are added here after the complete evaluation run. Raw answers, source IDs and timing records are saved in [eval/results](eval/results).

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

## Deployment and remaining work

The app has been tested locally. **A public deployment URL is not available yet.** [deployment.md](deployment.md) explains how to run it on a server. GitHub Pages cannot host this Python service.

Before submitting: get the instructor's approval for the corpus, collect real classmate feedback, review the question set and model grades, and add the actual live URL. No approval, user feedback or human grades have been invented.

## Contributions

Project owner: Lassad Boubarma. The implementation and draft documentation were prepared with coding-assistant support. The Project 1 model-calling code comes from the linked SQL Explanation Grader. Review the code and update this section with the team's actual contributions before submission.

The source text belongs to the Python documentation contributors. Its license and the text-processing changes are described in [data/README.md](data/README.md).
