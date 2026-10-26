# Finish the live measurements and GitHub submission

The ZIP has the complete source, saved baseline, written reports, and a three-page PDF. The live parts below require a real machine with Ollama. No P1 correctness or cache-speedup figure has been invented.

## What you need

- Python **3.11 or 3.12**, Git and [Ollama](https://ollama.com/) installed.
- Enough disk and RAM for dependencies, Qwen 2.5 3B, and the separate Qwen 2.5 7B grader. The earlier tests were done on Windows with 16 GB RAM and an RTX 3060. Reproduction on another machine is an independent result, not the old run.
- Internet to download Python packages, model weights and the pinned Project 1 Git repository.

## One-time setup and app

Open a terminal in the repository folder, with Ollama running:

```sh
python setup_project.py
python run.py
```

Open http://127.0.0.1:8000 and try `How can I read a file with pathlib?`, then `What is the university Wi-Fi password?` (it should refuse). Check that each linked quotation actually justifies the claim.

## Complete grading, cache timing and reports

In a separate terminal, from the repository folder:

```sh
python run.py -m unittest discover -s tests -v
python run.py -m eval.generation --split all
python run.py -m eval.benchmark --split all --baseline eval/results/generation.json
ollama pull qwen2.5:7b
python run.py -m eval.p1_judge --input eval/results/generation.json
```

Then regenerate the PDF and README tables using the virtual-environment Python:

**macOS / Linux**

```sh
.venv/bin/python continuation/make_deliverables.py
```

**Windows PowerShell**

```powershell
.venv\Scripts\python.exe continuation\make_deliverables.py
```

The grader is pinned to Project 1 commit `23473e6998e69718b32ec7c8963d0cfa86a23fdb` and judges all 112 answers. A failed call is excluded from full-set rates; rerun the command to resume successful judgments. The benchmark writes `benchmark_progress.json` after each question; rerun it if interrupted. Check that `eval/results/p1_judge.json` reports `questions: 112` and `errors: 0`, and that `benchmark.json` has the same code and model metadata as the freshly regenerated `generation.json`.

Do not run a new generator while benchmarking. Preserve `generation.json`, `p1_judge.json`, `benchmark.json`, `report.md`, `report.pdf`, `optimisation.md`, and `README.md` after rerunning them. Make sure `report.pdf` is still **six pages or fewer**.

## Publish without destroying other work

The GitHub repository was found to have **no branches** at inspection time, but check again before pushing.

**Easiest path to preserve the prepared local commit:** download `LibrarianRAG-finished.bundle` alongside this project ZIP, then run these commands from the directory containing the downloaded bundle:

```sh
git clone -b main LibrarianRAG-finished.bundle LibrarianRAG
cd LibrarianRAG
git remote set-url origin https://github.com/LassadBoubarma/LibrarianRAG.git
git push -u origin main
```

The bundle contains a verified **local** commit, not a GitHub commit. The index is ignored by Git and is rebuilt by the setup script. If the remote has gained commits, the push will be rejected; do not force-push. This bundle route is an alternative to creating a new commit from the ZIP, not an extra step.

Alternatively, use the following commands for an *empty* remote and an extracted ZIP folder with no Git history: 

```sh
git init -b main
git remote add origin https://github.com/LassadBoubarma/LibrarianRAG.git
git add .
git commit -m "Complete LibrarianRAG project and evaluation reports"
git push -u origin main
```

There is **no `--force`**. If Git reports that `main` already exists, do **not** force push. Clone the repository to a new folder, copy your project files into it without copying `.git`, commit there and push on top of the existing history. Do not commit model caches, `.venv`, or credentials. The `index/` directory is intentionally ignored: `setup_project.py` rebuilds it from the committed document snapshot.

After a successful push, open `https://github.com/LassadBoubarma/LibrarianRAG/commits/main` and copy the link to the final commit. If you later rerun the live results, commit and push the newly generated files too.

## Before the class demo

1. Obtain instructor approval for this corpus and record it truthfully.
2. Ask actual classmates to test it; use the anonymous feedback form in `data/feedback.csv`. Do not invent their feedback.
3. Read individual model verdicts and fill in the human-review columns only after a real review. Explain disagreements.
4. Arrange a server with Ollama and an HTTPS address using `deployment.md`, then test the external URL. GitHub Pages cannot run this service.
5. Review the code and contributions section. Use `explain.md` for the file-by-file walkthrough and demo plan.

Until those steps are completed, the project is a documented local prototype with saved experiments, **not** a fully deployed, user-validated service.
