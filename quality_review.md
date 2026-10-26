# Answer-quality review

This review uses the **112 saved answers from 19 October 2026**. It does not pretend that the model was run again. The full Project 1 model judge and human grading are still pending. The changes in `answer.py` were made afterwards, so none of the figures below is evidence that those changes improved accuracy.

## What the saved measurements mean

- 112 questions: 102 have annotated source answers; 10 are intentionally outside the corpus.
- On the 102 answerable questions, 95 received an answer and 7 were refused.
- All 10 out-of-scope questions were refused.
- The gold annotated evidence was cited for 67 of 102 answerable questions (65.7%). This is not the same as the cited passage being a valid justification.
- The source quote was copied exactly in every answered response; this is a mechanical source-integrity check, **not a faithfulness score**.
- Average token F1 was 0.314. Short correct answers can have low F1 when differently worded, so this is not a semantic correctness score.
- The five Project 1 trial judgments in `eval/results/earlier_trial/` are from a previous version. They do not grade these 112 answers.

## Specific failures in the saved answers

| ID | User question, shortened | Saved answer problem | What the docs support |
| --- | --- | --- | --- |
| q002 | `all` on empty input | Says `all` returns a *start value*. It cites `math.prod` instead of `all`. | `all([])` is `True`. |
| q005 | Number of items | Gives a dictionary-only description rather than naming `len`. | `len(obj)` gives the number of items. |
| q014 | Does `Path.write_text` overwrite? | Cites `Path.read_text` and never answers yes or no. | `Path.write_text` overwrites an existing file. |
| q017 | File extension of a path | Suggests `suffixes`, a list of extensions, instead of the single `suffix`. | Use `suffix` for the final extension. |
| q028 | CSV row writer | Answers `csv.DictWriter` to a question whose expected API is `csv.writer`. | Use `csv.writer` to write ordinary row sequences. |
| q033 | Format from `date.isoformat` | Cites `date.fromisoformat` and answers with that method's signature. | Typical output format is `YYYY-MM-DD`. |
| q041 | Concatenate several iterables | Says `zip` concatenates iterables; `zip` actually iterates in parallel. | Use `itertools.chain`. |
| q101 | Insert before equal list entries | Names `bisect_left`, which finds an insertion position but does not insert. | Use `bisect.insort_left`. |
| q102 | Insert after equal entries | Gives `bisect_left`, which instead locates before equal entries. | Use `bisect.insort_right`. |

These are concrete examples, not an exhaustive manually scored pass over all 112. Their IDs can be found in `eval/results/generation.json`, which retains the full answer and copied evidence.

## Changes made after the saved run

- The prompt now explicitly warns against confusing similarly named functions.
- For a question that names a dotted API, the selected passage must mention at least one of those dotted APIs. This is deliberately a small safeguard, not a semantic verifier. It can still refuse valid answers or accept bad interpretations.
- Several equivalent refusal phrases now count as abstentions rather than appearing as sourced answers.
- Bad API request JSON produces a 400 response instead of risking a server error.

**Next quality checks:** rerun `eval.generation` on the same 112 questions, run the pinned Project 1 judge on all of them, read the per-question reasons, and have people independently check correctness and whether the cited text justifies the answer. Do not claim an improvement until after the new measurements. If you revise the questions or tune the retrieval on them, create a fresh held-out set for an honest comparison.
