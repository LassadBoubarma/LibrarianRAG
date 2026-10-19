"""Save actual answers, automatic checks, and blank columns for human grading."""
import argparse
import csv
import re
from collections import Counter

from answer import Librarian, normalize
from eval.common import RESULTS, metadata, percentiles, questions, relevant, save
from search import Search


def token_f1(actual, expected):
    def words(text):
        return Counter(re.findall(r"[a-z0-9_]+", re.sub(r"\[\d+\]", "", text.lower())))
    a, b = words(actual), words(expected)
    overlap = sum((a & b).values())
    return 2 * overlap / (sum(a.values()) + sum(b.values())) if a and b else 0


def summarize(rows):
    answerable = [r for r in rows if r["answerable"]]
    unknown = [r for r in rows if not r["answerable"]]
    answered = [r for r in rows if not r["result"]["abstained"]]
    return {"questions": len(rows), "answerable_questions": len(answerable),
            "answer_token_f1": sum(r["token_f1"] for r in answerable) / len(answerable),
            "gold_citation_rate_all_answerable": sum(r["gold_citation"] for r in answerable) / len(answerable),
            "exact_quote_rate_answered": sum(r["quote_valid"] for r in answered) / len(answered) if answered else None,
            "abstention_accuracy_unanswerable": sum(r["result"]["abstained"] for r in unknown) / len(unknown) if unknown else None,
            "answer_coverage": len([r for r in answerable if not r["result"]["abstained"]]) / len(answerable),
            "human_correctness": None, "human_faithfulness": None,
            "note": "Token F1 and quote existence are automatic proxies, not human correctness or faithfulness.",
            **percentiles([r["result"]["latency_ms"] for r in rows])}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=["all", "dev", "test"], default="test")
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    librarian = Librarian(Search())
    librarian.ask("How do I read a text file with pathlib?", use_cache=False)
    rows = []
    for q in questions(args.split)[:args.limit]:
        result = librarian.ask(q["question"], use_cache=False)
        rows.append({**q, "result": result, "token_f1": token_f1(result["answer"], q["answer"]),
                     "gold_citation": q["answerable"] and any(relevant(c, q) for c in result["sources"]),
                     "quote_valid": bool(result["sources"]) and all(normalize(c["quote"]) in normalize(c["text"]) for c in result["sources"])})
        print(f"{q['id']}: {result['answer']}", flush=True)
    save("generation.json", {"split": args.split, "metadata": metadata(), "summary": summarize(rows),
                             "by_split": {split: summarize([r for r in rows if r["split"] == split])
                                          for split in {r["split"] for r in rows}}, "rows": rows})
    with (RESULTS / "human_review.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["id", "question", "expected", "actual", "quote", "correct_0_or_1", "faithful_0_or_1", "citation_supports_claim_0_or_1", "notes"])
        for r in rows:
            writer.writerow([r["id"], r["question"], r["answer"], r["result"]["answer"], " | ".join(c["quote"] for c in r["result"]["sources"]), "", "", "", ""])
