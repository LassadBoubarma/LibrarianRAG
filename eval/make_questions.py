"""Attach real source passages to the hand-written question seeds."""
import csv
import json

from settings import DATA


def main():
    records = {r["id"]: r for r in map(json.loads, (DATA / "documents.jsonl").read_text(encoding="utf-8").splitlines())}
    rows, errors = [], []
    with (DATA / "question_seeds.tsv").open(encoding="utf-8") as file:
        for number, (doc, anchor, question, answer, needle) in enumerate(csv.reader(file, delimiter="\t"), 1):
            source_id = f"{doc}#{anchor}"
            record = records.get(source_id)
            if not record or needle.lower() not in record["text"].lower():
                errors.append(f"{number}: {source_id}: missing {needle!r}")
                continue
            position = record["text"].lower().index(needle.lower())
            start = record["text"].rfind("\n\n", 0, position) + 2
            if start == 1:
                start = 0
            end = record["text"].find("\n\n", position)
            if end == -1:
                end = len(record["text"])
            rows.append({"id": f"q{number:03}", "question": question, "answer": answer,
                         "source_id": source_id, "source_url": record["url"],
                         "source_passage": record["text"][start:end],
                         "evidence_start": position, "evidence_end": position + len(needle),
                         "answerable": True, "split": "dev" if number % 5 == 0 else "test"})
    if errors:
        raise SystemExit("\n".join(errors))
    unknowns = ["What is the weather in Tunis tomorrow?", "What is my university Wi-Fi password?",
                "Who won the football match last night?", "What are my grades this semester?",
                "How do I make a pizza?", "What is the price of Bitcoin right now?",
                "What is the deadline for my CS496 homework?", "What is my student ID?",
                "Who is teaching my class next week?", "Which bus should I take home today?"]
    for number, question in enumerate(unknowns, 1):
        rows.append({"id": f"u{number:03}", "question": question,
                     "answer": "I don't know based on these documents.", "answerable": False,
                     "source_id": None, "source_passage": None, "split": "test"})
    (DATA / "questions.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    print(f"Saved {len(rows)} questions ({len(rows) - len(unknowns)} with source passages)")


if __name__ == "__main__":
    main()
