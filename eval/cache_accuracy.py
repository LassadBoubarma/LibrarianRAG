"""Grade changed cached answers; reuse grades when answer and evidence are identical."""
import json

from eval.common import RESULTS, save
from eval.p1_judge import RagVerdict, load_p1
from settings import ROOT


def signature(result):
    return (result["answer"], result["abstained"],
            [(c["source_id"], c["quote"]) for c in result["sources"]])


if __name__ == "__main__":
    generation = json.loads((RESULTS / "generation.json").read_text(encoding="utf-8"))
    benchmark = json.loads((RESULTS / "benchmark.json").read_text(encoding="utf-8"))
    original_grades = json.loads((RESULTS / "p1_judge.json").read_text(encoding="utf-8"))
    grades = {r["id"]: r for r in original_grades["rows"]}
    cached = benchmark["outputs"]["cache_repeated"]
    if benchmark["metadata"] != generation["metadata"]:
        raise ValueError("The benchmark and generation run use different implementations")
    if len(cached) != len(generation["rows"]) or original_grades["summary"]["errors"]:
        raise ValueError("Complete generation, benchmark and P1 grading first")
    call_json = load_p1(ROOT / "work" / "p1")
    prompt = (ROOT / "eval" / "judge_prompt.md").read_text(encoding="utf-8")
    model = original_grades["summary"]["judge_model"]
    rows = []
    for question, result in zip(generation["rows"], cached):
        before = grades[question["id"]]
        if before["input"] != question["question"] or before["output"] != question["result"]["answer"]:
            raise ValueError("P1 grades do not match the baseline answers")
        unchanged = signature(result) == signature(question["result"])
        if unchanged:
            verdict = before["verdict"]
            reason = before["reason"]
        else:
            payload = {"question": question["question"], "expected_answer": question["answer"],
                       "answerable": question["answerable"], "reference_passage": question["source_passage"],
                       "actual_answer": result["answer"], "abstained": result["abstained"],
                       "cited_quotes": [c["quote"] for c in result["sources"]],
                       "cited_passages": [c["text"] for c in result["sources"]]}
            judged, usage = call_json(model, prompt, json.dumps(payload), RagVerdict, seed=42)
            verdict, reason = judged.model_dump(), judged.reason
            if result["abstained"]:
                verdict["correct"] = not question["answerable"]
            print(f"Regraded {question['id']}: {reason}", flush=True)
        rows.append({"id": question["id"], "answerable": question["answerable"],
                     "baseline_score": before["score"], "cached_score": int(verdict["correct"]),
                     "grade_reused": unchanged, "cached_answer": result["answer"],
                     "verdict": verdict, "reason": reason})
    answerable = [r for r in rows if r["answerable"]]
    before = sum(r["baseline_score"] for r in answerable) / len(answerable)
    after = sum(r["cached_score"] for r in answerable) / len(answerable)
    change = 100 * (after - before)
    save("cache_accuracy.json", {"summary": {
        "questions": len(rows), "answerable_questions": len(answerable), "judge_model": model,
        "baseline_correctness_answerable": before, "cached_correctness_answerable": after,
        "change_percentage_points": change, "meets_max_two_point_loss": change >= -2,
        "reused_grades": sum(r["grade_reused"] for r in rows),
        "new_judge_calls": sum(not r["grade_reused"] for r in rows),
        "note": "Model judgments. A grade is reused only when answer, refusal status and cited evidence match exactly."
    }, "rows": rows})
