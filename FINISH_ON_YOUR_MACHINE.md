# Before the class submission

The local implementation, measured evaluation and report are included. Start with `START_HERE.md` for setup and `README.md` for results. The public repository is https://github.com/LassadBoubarma/LibrarianRAG.

The team still needs to:

1. Get instructor approval for the corpus.
2. Ask real classmates to test the app and collect anonymous feedback in `data/feedback.csv`.
3. Review the model grades and fill the human-review CSV after reading the answers and citations.
4. Provide a host, deploy with Ollama using `deployment.md`, and add the tested public URL.
5. Review the code and record the team's actual contributions before presenting.

To repeat the measurements, use the commands in `eval/README.md`. The optional report builder is `continuation/make_deliverables.py`; it requires ReportLab (`python -m pip install reportlab==4.4.9`). Review the regenerated PDF and keep it within six pages.

The GitHub push is a normal merge that preserves both the desktop and web histories. Never force-push over someone else's work.
