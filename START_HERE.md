# Continue this project

## Request
Build CS496 Project 2 from the included assignment PDF. Keep the Python code and README wording simple and easy for the student to explain. The chosen idea is a Python documentation question-answering service. Do not claim that the student personally wrote or tested work they have not reviewed.

Target repository: https://github.com/LassadBoubarma/LibrarianRAG
Project 1: https://github.com/BLACK2202/sql-explanation-grader
P1 revision: 23473e6998e69718b32ec7c8963d0cfa86a23fdb

## Snapshot status (packaged 26 October 2026)
The implementation and measurements were made on 19 October. The app was tested locally in a browser, and nine automated checks passed. Source code was committed locally, but was NOT pushed to GitHub. A dry-run push confirmed access at the time. The remote had no branches when this ZIP was prepared.

The app uses Flask, BM25, MiniLM embeddings, a MiniLM cross-encoder, and Ollama Qwen 2.5 3B. It searches 25 official Python 3.14.0 documentation pages (209,222 words). The chosen index has 3,297 chunks, 180 tokens per chunk, no overlap. The cleaned corpus, license, questions and built index are included.

## Completed measurements
- 102 drafted answerable questions with actual source passages, plus 10 out-of-scope questions.
- Full retrieval ablation: keyword recall@5 73.5%, vector 63.7%, hybrid 84.3%, reranked 91.2%.
- Full generation run: 112 answers saved in eval/results/generation.json. This is the current implementation's run.
- Generation token F1: 0.314 (word overlap, NOT semantic correctness).
- Gold-passage citation rate: 65.7%; answer coverage: 93.1%; out-of-scope refusal: 10/10.
- The generated answers include real mistakes. Do not describe the app as fully accurate.
- Chunking comparison and observed model versions are saved in eval/results/.

## Important unfinished work
1. The cache benchmark was interrupted. There is NO completed benchmark.json. Do not invent speedup numbers.
2. eval/results/earlier_trial/p1_judge.json contains only FIVE development-trial grades from an older implementation. It is NOT a grade of the current 112 answers. Re-run eval.p1_judge against generation.json before reporting correctness or faithfulness.
3. README.md still has a results placeholder. optimisation.md, report.md and report.pdf were not generated. README links to them are currently incomplete.
4. A draft report generator is included at continuation/make_deliverables.py. It needs completed benchmark and current P1 results first; review its claims and verify the PDF layout before delivery.
5. A clean checkout was prepared, but its full setup test was NOT completed. Verify setup, tests and run commands.
6. No public deployment, instructor approval, real user feedback or human grading has been completed. The feedback CSV and human review grading columns are intentionally blank.
7. No hosting account was supplied. GitHub alone cannot run this Python/Ollama service.
8. The final project still needs to be pushed to the target repository if the user wants that. This ZIP contains no Git history or credentials.

## Commands after extraction
Install Python 3.11 or 3.12 and Ollama, then start Ollama.
Run `python setup_project.py` (Windows alternative: `py -3.11 setup_project.py`).
Run `python run.py` and open http://127.0.0.1:8000.

To continue evaluation:
```
python run.py -m unittest discover -s tests -v
python run.py -m eval.generation --split all
python run.py -m eval.benchmark --split all --baseline eval/results/generation.json
ollama pull qwen2.5:7b
python run.py -m eval.p1_judge
```
Regenerate the baseline when changing machines or code: the benchmark checks environment and implementation metadata. The P1 adapter downloads a pinned checkout and imports its actual call_json helper. The old SQL rubric is replaced by eval/judge_prompt.md.

## Useful files
Read explain.md, then settings.py, corpus.py, build_index.py, search.py, answer.py and app.py. The source PDF is in reference/project2-librarian.pdf. The report draft script needs reportlab, which is not a runtime dependency of the app. A previous browser screenshot is included under reference/.

The ZIP excludes virtual environments, downloaded model weights, raw HTML, Git credentials/history and scratch indexes. Setup downloads the required models. ChatGPT web may be able to review and edit the code, but local Ollama execution still needs a suitable computer or server.
