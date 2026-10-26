# Postmortem

This is the implementation postmortem. Classmate testing and a public deployment have not happened yet, so it does not claim lessons from either.

## Source links were less simple than expected

The Python docs sometimes put several function signatures above one explanation. The first parser attached text to the last name, which broke some question references. The parser now uses the first signature. Tests check this case. Some methods still use a shared anchor, such as the generic sequence copy method.

## Asking the model to copy a quote caused unnecessary refusals

The first version asked a 1.5B model to write an answer and copy a quote. It sometimes paraphrased the quote. The exact-match check then rejected an otherwise useful answer. The final version copies the selected passage directly from the index. This makes the evidence real, but does not prove the interpretation is right. The intermediate 3B answer model also confused similar APIs and refused answerable development questions; the final version uses 7B. It needs more memory, but keeps the code the same.

## Retrieval and answer quality are different

Some simple questions retrieve a nearby API instead of the intended one. Even a correct passage can be ignored by the model. The results therefore keep search recall, answer overlap, citation location and model-judged correctness separate. The final tables report what happened, including misses.

## The grader can be wrong too

In the Project 1 integration trial, the judge described a refusal as appropriate even though the question was marked answerable. The adapter now applies the known refusal rule directly and preserves the raw judgment for inspection. Other semantic judgments still need review. Using an LLM as a judge does not replace reading a sample of its results.

## A warm cache is a special workload

Repeated questions can avoid all model work. New questions cannot. The optimisation report separates those workloads and includes the first-use cost. A claim about the whole service needs a real distribution of student questions and a real cache hit rate.

## What is left

Get approval for the corpus, ask classmates to test the service, review the drafted questions and judge labels, and deploy on an actual host. Use their failures to improve the small system before adding more libraries or features. The code and draft documentation were prepared with coding-assistant support; the project owner still needs to review and understand them before presenting.
