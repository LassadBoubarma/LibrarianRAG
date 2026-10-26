# How to explain the project

Start with this: “I built a helper for Python documentation. It searches the docs first, then gives the model a few useful passages. The answer includes a quote so the user can check it.”

## Read the code in this order

| File | What to understand |
| --- | --- |
| `settings.py` | Paths and model names. |
| `corpus.py` | Download documents and remember where each section came from. |
| `build_index.py` | Split text, turn chunks into vectors, save them. |
| `search.py` | Find candidates in two ways and rerank them. |
| `answer.py` | Ask the model, check its evidence, cache the result. |
| `app.py` | Receive a question and return an answer. |
| `eval/` | Check retrieval and answers separately. |

An embedding is a list of numbers representing text. Similar text tends to have similar vectors. BM25 is keyword search: it is useful for exact names such as `read_text`. Hybrid search combines their rankings. A reranker spends more time comparing the question with a small set of candidates.

RAG means retrieval-augmented generation. We do not train the answer model on the docs. We search the docs and put useful text in its prompt.

## A simple demo

1. Ask “How do I read a file as text with pathlib?”
2. Open the linked documentation and compare the quote.
3. Ask the same question again to show the cache.
4. Ask “What is my university Wi-Fi password?” to show refusal.
5. Show the ablation table and explain which search method found more correct passages.

Recall@5 asks whether the correct evidence is among the first five results. Faithfulness asks whether the answer follows from the evidence. They are different: finding the right text does not guarantee a correct answer.

## Questions to be ready for

**Why no vector database?** A few thousand vectors fit in memory. NumPy is enough and easy to inspect.

**Why use two searches?** Keywords handle exact API names; vectors help with different wording.

**Does a citation guarantee truth?** No. We check that the quote exists, but a person still needs to check whether it supports the answer.

**Why is a cached answer faster?** It avoids both retrieval and generation. A new question still needs those steps.

**What would you improve next?** Collect real student questions, grade the answers, and work on refusals and table parsing before adding features.

Read and run the code before presenting it. The evaluation numbers describe this implementation, not work you should claim to have personally carried out without reviewing it.
