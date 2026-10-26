"""A small browser form and JSON endpoint."""
import os
from threading import Lock

import requests
from flask import Flask, jsonify, render_template, request
from waitress import serve

from answer import Librarian
from search import Search


def create_app(librarian=None):
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = 4096
    librarian = librarian or Librarian(Search())
    lock = Lock()  # One model request at a time on a student laptop.

    @app.get("/")
    def home():
        return render_template("index.html", documents=librarian.search.documents)

    @app.get("/health")
    def health():
        return jsonify(status="ok", index_loaded=True)

    @app.post("/ask")
    def ask():
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify(error="Send a JSON object."), 400
        question = data.get("question")
        document = data.get("document") or None
        if not isinstance(question, str) or not 3 <= len(question.strip()) <= 500:
            return jsonify(error="Write a question between 3 and 500 characters."), 400
        if document is not None and document not in librarian.search.documents:
            return jsonify(error="Choose a document from the list."), 400
        if not lock.acquire(blocking=False):
            return jsonify(error="Another question is running. Try again shortly."), 503
        try:
            return jsonify(librarian.ask(question.strip(), document))
        except requests.RequestException:
            return jsonify(error="The local language model is unavailable. Check that Ollama is running and the model is installed."), 503
        finally:
            lock.release()

    return app


if __name__ == "__main__":
    serve(create_app(), host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", "8000")), threads=4)
