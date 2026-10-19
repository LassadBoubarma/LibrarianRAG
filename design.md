# Design

The project answers questions about the Python 3.14.0 standard library. The intended users are students learning Python. This is a proposed corpus choice; instructor approval and student feedback still need to be collected.

## Documents

`corpus.py` reads 25 official documentation pages. These are long reference documents, not 25 short articles: the extracted text has 209,222 words, about 418 pages at 500 words per page. That page count is an estimate, not a PDF page count. `data/manifest.json` records the release URL, download time and hashes. The cleaned snapshot is committed so a new checkout gets the same text.

Each section keeps its title, URL, anchor, author and release date. Paragraphs and table rows become plain text. Code blocks retain their line breaks. Navigation is removed. The Python license is in `data/PYTHON-LICENSE.txt`; the changes are HTML removal, whitespace cleanup and division into sections.

## Index

The default is 180 tokenizer tokens per chunk with no overlap. A chunk never crosses a section. Token boundaries keep the text below MiniLM's 256-token input limit. Very long code blocks can still be split. `eval/chunking.py` compared 120/24, 180/0 and 180/36 on 20 development questions: recall@5 was 85%, 90% and 90%. We chose 180/0 because it matched the overlapping version with fewer chunks. This small development set does not prove overlap is never useful.

MiniLM converts each chunk to a vector of 384 numbers. The vectors are normalized and stored in a NumPy file. Chunks are stored in JSON. At this size a vector database would add setup work without solving a problem we have. No pickle files are loaded.

## Search

1. BM25 finds chunks with matching words and identifiers.
2. Vector search finds chunks with similar meaning.
3. Reciprocal rank fusion combines the top 30 from each list. Each position contributes `1 / (60 + rank)`.
4. A MiniLM cross-encoder reads the question and each of the top 20 chunks together, then orders them again.
5. The best five chunks go to the answer model.

The document filter is applied before ranking. There is no question rewriting: a single explicit question is easier to debug, and rewriting adds a model call. Follow-up questions need to include their context.

## Answer

Ollama runs Qwen 2.5 3B locally. It is asked for a short answer and one source number using a JSON schema. The server checks that the source number exists and copies that whole passage from the index as evidence. The model never supplies the displayed quote. Low retrieval scores (below -3), a refusal or an invalid source return “I don't know based on these documents.” The cutoff is a heuristic, not a calibrated probability.

Copying a real passage cannot prove that a paraphrase follows from it. Human faithfulness review is therefore a separate task. The app renders text using `textContent`, so model output is not interpreted as HTML. It never executes suggested Python code.

## Cache and service

An in-memory LRU cache stores up to 128 answers. The key includes the exact trimmed question, document filter and model name. Restart after changing the index or model. There is one active model request at a time; other requests receive a useful 503 response. This keeps memory use predictable on a laptop, but it is not a high-traffic design.

## Known limits

- Flattened tables lose some relationships between columns.
- Code may be split in the middle of a block.
- Cross-references are not followed automatically.
- The small model sometimes refuses a question that has an answer.
- A real quote can be paired with a wrong interpretation.
- The corpus is a fixed release, not the latest online Python docs.
- The evaluation mostly asks short API questions. It does not represent all beginner questions.
- Source spans name one accepted passage. An equally valid passage elsewhere can be counted as a miss.
