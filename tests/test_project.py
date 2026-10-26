import json
import unittest
from unittest.mock import Mock, patch

import requests

from answer import Librarian, generate
from app import create_app
from corpus import extract
from eval.common import questions
from settings import DATA, UNKNOWN


class ProjectTests(unittest.TestCase):
    def setUp(self):
        self.chunk = {"id": "test:0", "text": "Return the decoded contents of the file as a string.",
                      "section": "Path.read_text", "score": 5, "url": "https://docs.python.org/", "document": "pathlib"}

    def response(self, answer="Use Path.read_text.", source=1, quote="decoded contents of the file"):
        response = Mock()
        response.json.return_value = {"message": {"content": json.dumps({"answer": answer, "source": source, "quote": quote})}}
        return response

    def test_evidence_is_copied_from_source_not_model(self):
        with patch("answer.requests.post", return_value=self.response(quote="a made up statement")):
            result = generate("How?", [self.chunk])
        self.assertEqual(result["sources"][0]["quote"], self.chunk["text"])

    def test_rejects_out_of_range_citation(self):
        with patch("answer.requests.post", return_value=self.response(source=9)):
            self.assertTrue(generate("How?", [self.chunk])["abstained"])

    def test_valid_quote_and_citation(self):
        with patch("answer.requests.post", return_value=self.response()):
            result = generate("How?", [self.chunk])
        self.assertFalse(result["abstained"])
        self.assertEqual(result["answer"], "Use Path.read_text. [1]")

    def test_weak_retrieval_skips_model(self):
        with patch("answer.requests.post") as post:
            result = generate("Weather?", [{**self.chunk, "score": -9}])
            post.assert_not_called()
        self.assertEqual(result["answer"], UNKNOWN)

    def test_cache_respects_document_filter_and_eviction(self):
        search = Mock()
        search.retrieve.return_value = ([self.chunk], 10)
        librarian = Librarian(search, cache_size=1)
        with patch("answer.requests.post", return_value=self.response()):
            first = librarian.ask("How?", "pathlib")
            self.assertTrue(librarian.ask("How?", "pathlib")["cache_hit"])
            self.assertFalse(librarian.ask("How?", "os")["cache_hit"])
            self.assertFalse(librarian.ask("How?", "pathlib")["cache_hit"])
        self.assertEqual(len(librarian.cache), 1)
        self.assertFalse(first["cache_hit"])

    def test_api_rejects_invalid_input(self):
        librarian = Mock()
        librarian.search.documents = ["pathlib"]
        client = create_app(librarian).test_client()
        for data in [[], {}, {"question": 42}, {"question": "x"}, {"question": "x" * 501}, {"question": "How?", "document": "missing"}]:
            self.assertEqual(client.post("/ask", json=data).status_code, 400)
        librarian.ask.assert_not_called()

    def test_api_reports_model_outage(self):
        librarian = Mock()
        librarian.search.documents = ["pathlib"]
        librarian.ask.side_effect = requests.ConnectionError()
        client = create_app(librarian).test_client()
        self.assertEqual(client.post("/ask", json={"question": "How?"}).status_code, 503)

    def test_api_serves_cache_hits_without_locking(self):
        search = Mock()
        search.documents = ["pathlib"]
        librarian = Librarian(search)
        cached_result = {"answer": "Use Path.read_text. [1]", "sources": [self.chunk],
                         "abstained": False, "reason": "answered", "input_tokens": 0, "output_tokens": 0}
        librarian.cache[("How?", None, "qwen2.5:7b")] = cached_result

        client = create_app(librarian).test_client()
        res = client.post("/ask", json={"question": "How?"})
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.get_json()["cache_hit"])
        search.retrieve.assert_not_called()

    def test_definition_aliases_keep_primary_anchor(self):
        html = '<div class="body"><h1>Example</h1><section id="s"><h2>Section</h2><dl><dt id="first">first()</dt><dt id="alias">alias()</dt><dd><p>Same explanation.</p></dd></dl></section></div>'
        records = extract(html, "example")
        self.assertEqual(records[0]["id"], "example#first")
        self.assertEqual(records[0]["text"].strip(), "Same explanation.")

    def test_eval_passages_exist_in_corpus(self):
        records = {r["id"]: r for r in map(json.loads, (DATA / "documents.jsonl").read_text(encoding="utf-8").splitlines())}
        answerable = [q for q in questions() if q["answerable"]]
        self.assertGreaterEqual(len(answerable), 100)
        for q in answerable:
            record = records[q["source_id"]]
            self.assertIn(q["source_passage"], record["text"])
            self.assertGreater(q["evidence_end"], q["evidence_start"])


if __name__ == "__main__":
    unittest.main()
