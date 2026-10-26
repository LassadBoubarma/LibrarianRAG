# Answer quality

The current answers and model grades are in `eval/results/generation.json` and `eval/results/p1_judge.json`. Read the individual source passages as well as the totals in README.md.

The earlier 3B-model review is preserved in `reference/quality_review_2026-10-19.md`. Its saved answers are now in `eval/results/baseline_2026-10-19/generation.json`. The problems listed in that historical review must not be presented as results from the final model.

## Changes in the final version

- Qwen 2.5 7B replaces the smaller answer model.
- The prompt warns about similar API names.
- A question naming a dotted API must cite evidence mentioning at least one of those API names. This is a simple safeguard, not a semantic verifier.
- Common refusal phrases are treated as refusals.
- The full P1 grader and cache-accuracy comparison use all 112 saved answers.

## What to review manually

Check similar names such as `suffix` versus `suffixes`, `chain` versus `zip`, and insertion positions versus actual insertion in `bisect`. A passage can mention the right API while the answer still misunderstands it. Documentation examples can also define helper functions that are not public APIs.

The generator and judge use the same model. The judge has made contradictory decisions and can penalize valid short answers. The rubric now explicitly accepts short answers, but the grades still need independent review. The empty human-review columns must only be filled after someone reads the answers and evidence.
