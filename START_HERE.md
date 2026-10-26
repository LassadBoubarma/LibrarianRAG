# Start here

This is the Python documentation helper for CS496 Project 2. It searches the Python 3.14.0 standard-library reference and answers with a linked source passage.

## Run

Install Python 3.11 or 3.12, Git and Ollama. Start Ollama, then open a terminal in this folder.

Setup:

```sh
python setup_project.py
```

On Windows with multiple Python versions, use `py -3.11 setup_project.py`.

Run:

```sh
python run.py
```

Open http://127.0.0.1:8000. Setup downloads the Python dependencies and local models; model weights and virtual environments are not included in the ZIP.

## Read

- `README.md`: setup, measured results and project structure.
- `explain.md`: how the code works and a short presentation plan.
- `report.pdf` and `report.md`: the project report.
- `optimisation.md`: cache measurements and cost assumptions.
- `eval/results/`: all saved answers, grades and benchmark records.
- `postmortem.md`: actual implementation problems and limitations.

The Project 1 grading adapter uses the pinned public repository at https://github.com/BLACK2202/sql-explanation-grader. The main project repository is https://github.com/LassadBoubarma/LibrarianRAG.

## Before final submission

The implementation can be tested automatically, but instructor approval and real classmate feedback must come from the team. The feedback form is blank, and the human grading columns are blank. Model judgments are clearly labeled and may be wrong.

A public hosting account has not been supplied. The app runs locally; `deployment.md` explains server deployment. Add a real public URL after deploying and checking it. A GitHub repository link is not a live question-answering service.

Read and run the code before presenting. Contributions should describe what each team member actually did.
