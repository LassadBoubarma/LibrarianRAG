"""Fast tests that work without Ollama, Flask, embeddings or downloaded models."""
import json
import unittest
from unittest.mock import Mock, patch

from answer import Librarian, generate
from settings import UNKNOWN


class OfflineTests(unittest.TestCase):
    def setUp(self):
        self.chunk = {"id": "pathlib#read_text:0", "section": "Path.read_text",
                      "text": "Path.read_text() returns the decoded contents of the file.",
                      "score": 4.0, "document": "pathlib"}

    def response(self, answer, source=1):
        result = Mock()
        result.json.return_value = {"message": {"content": json.dumps({"answer": answer, "source": source})}}
        return result

    def test_full_quote_from_index(self):
        with patch("answer.requests.post", return_value=self.response("Use Path.read_text().")):
            result = generate("How do I call Path.read_text?", [self.chunk])
        self.assertEqual(result["sources"][0]["quote"], self.chunk["text"])

    def test_mismatched_api_citation_refused(self):
        with patch("answer.requests.post", return_value=self.response("Use Path.read_text().")):
            result = generate("What does os.listdir do?", [self.chunk])
        self.assertTrue(result["abstained"])

    def test_api_name_with_html_extraction_spacing(self):
        spaced = {**self.chunk, "section": "Path. read_text", "text": "Return decoded text."}
        with patch("answer.requests.post", return_value=self.response("Use Path.read_text().")):
            result = generate("What does Path.read_text do?", [spaced])
        self.assertFalse(result["abstained"])

    def test_cannot_answer_is_refusal(self):
        with patch("answer.requests.post", return_value=self.response("I do not know from these passages.")):
            result = generate("How do I call Path.read_text?", [self.chunk])
        self.assertEqual(result["answer"], UNKNOWN)

    def test_cache_skips_search_on_hit(self):
        search = Mock()
        search.retrieve.return_value = ([self.chunk], 4.0)
        librarian = Librarian(search)
        with patch("answer.requests.post", return_value=self.response("Use Path.read_text().")) as post:
            first = librarian.ask("How do I call Path.read_text?")
            repeat = librarian.ask("How do I call Path.read_text?")
        self.assertFalse(first["cache_hit"])
        self.assertTrue(repeat["cache_hit"])
        self.assertEqual(search.retrieve.call_count, 1)
        self.assertEqual(post.call_count, 1)
        self.assertEqual(first["answer"], repeat["answer"])


if __name__ == "__main__":
    unittest.main()
