# Data

- `documents.jsonl`: cleaned Python 3.14.0 reference sections, with source metadata.
- `manifest.json`: download time, document hashes and corpus size.
- `PYTHON-LICENSE.txt`: upstream license and copyright notices.
- `question_seeds.tsv`: 102 drafted questions, answers and source lookup terms.
- `questions.jsonl`: those questions with actual source passages, plus 10 out-of-scope questions.
- `feedback.csv`: blank form for real user testing. It contains no invented feedback.

Every fifth answerable question is development data (20 questions). The remaining 82 and the 10 unanswerable questions form the test set. All paraphrases are drafted for this project; they are not collected from students. Review them before treating them as a final benchmark.

Run `python run.py -m eval.make_questions` to check the source references and rebuild the question file. Each evidence span identifies a relevant phrase inside the source passage. Retrieval counts a hit only when a chunk contains that span from the same source section.

The documents are public and contain no student records. Python documentation is licensed under the PSF License Version 2; examples also have the 0BSD option described in the included license. This project removes HTML and navigation, normalizes prose whitespace, preserves code text and divides the material into sections. Source text is not claimed as original work.

For user feedback, ask classmates to try their own questions. Record an anonymous label such as `student-1`, not their name or email. Do not enter passwords or personal information. Leave uncollected results blank.
