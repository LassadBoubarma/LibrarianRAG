"""Create the short report and README tables from measured results."""
import json
from pathlib import Path
from shutil import copyfile
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
RESULTS = ROOT / "eval/results"
read = lambda name: json.loads((RESULTS / name).read_text(encoding="utf-8"))
pct = lambda number: f"{100 * number:.1f}%" if number is not None else "not measured"
ablation = read("ablation.json")
generation = read("generation.json")["summary"]
judge = read("p1_judge.json")["summary"]
benchmark = read("benchmark.json")["results"]
chunking = read("chunking.json")
cache_accuracy = read("cache_accuracy.json")["summary"]
assert judge["questions"] == generation["questions"] == 112, "Complete the full generation and P1 grading runs first"

retrieval_rows = [[r["mode"], pct(r["recall_at_k"]), f"{r['p95_ms']:.1f} ms"] for r in ablation]
retrieval_table = "| Search | Recall@5 | Search p95 |\n| --- | --- | --- |\n" + "\n".join("| " + " | ".join(row) + " |" for row in retrieval_rows)
generation_rows = [
    ["Model-judged correctness (102 answerable)", pct(judge["model_judged_correctness_answerable"])],
    ["Model-judged correctness (all 112)", pct(judge["model_judged_correctness"])],
    ["Model-judged faithfulness (answered only)", pct(judge["model_judged_faithfulness_answered"])],
    ["Model-judged citation support (answered only)", pct(judge["model_judged_citation_support_answered"])],
    ["Answer coverage (102 answerable)", pct(generation["answer_coverage"])],
    ["Correct refusal (10 out-of-scope)", pct(generation["abstention_accuracy_unanswerable"])],
    ["Gold-passage citation rate (102 answerable)", pct(generation["gold_citation_rate_all_answerable"])],
    ["Answer token F1 (word-overlap proxy)", f"{generation['answer_token_f1']:.3f}"],
]
gen_table = "| Measure | Result |\n| --- | --- |\n" + "\n".join("| " + " | ".join(row) + " |" for row in generation_rows)
speed_rows = []
for key, name in [("baseline_no_cache", "No cache"), ("cache_first_use", "Cache, first use"), ("cache_repeated", "Cache, repeated")]:
    r = benchmark[key]
    speed_rows.append([name, f"{r['p50_ms']:.3f}", f"{r['p95_ms']:.3f}", str(r["cache_hits"]), str(r["input_tokens"] + r["output_tokens"])])
speed_table = "| Workload | p50 ms | p95 ms | Cache hits / 112 | Model tokens |\n| --- | --- | --- | --- | --- |\n" + "\n".join("| " + " | ".join(row) + " |" for row in speed_rows)
same_baseline = pct(benchmark["same_answer_rate_vs_baseline"])
same_first = pct(benchmark["same_answer_rate_vs_first_use"])
reduction = benchmark["p95_reduction_percent_repeated_only"]
accuracy_comparison = (
    f"On the 102 answerable questions, model-judged correctness was "
    f"{pct(cache_accuracy['baseline_correctness_answerable'])} before and "
    f"{pct(cache_accuracy['cached_correctness_answerable'])} after caching "
    f"({cache_accuracy['change_percentage_points']:+.2f} percentage points). "
    f"{cache_accuracy['new_judge_calls']} changed outputs were regraded; "
    f"{cache_accuracy['reused_grades']} grades were reused because answer and evidence matched exactly."
)

results_text = f"""Measured locally on 26 October 2026: Ryzen 5 5600X, 16 GB RAM, RTX 3060. Search runs on CPU; Ollama uses the GPU. Model warmup is excluded. Timings measure the local pipeline, not public HTTP load. The dataset has 102 answerable questions and 10 out-of-scope questions.

{retrieval_table}

{gen_table}

The P1 adapter uses Qwen 2.5 7B as a judge. The generator and judge use the same model, which can bias these scores. These are model judgments, not human grades. Copied passages exist by construction; that alone is not proof of faithfulness. All 112 questions are included in the descriptive results, including the 20 development questions. Raw answers and individual judge reasons are in [eval/results](eval/results).

{speed_table}

Repeated questions reduced p95 by {reduction:.4f}% in a 100% cache-hit workload. Answers matched the first-use responses {same_first} of the time and the separate no-cache run {same_baseline} of the time. {accuracy_comparison} This does not promise the same speedup for new questions. See [optimisation.md](optimisation.md)."""
readme = ROOT / "README.md"
text = readme.read_text(encoding="utf-8")
start = text.index("## Results\n") + len("## Results\n")
end = text.index("\n## Evaluation", start)
readme.write_text(text[:start] + "\n" + results_text + "\n" + text[end:], encoding="utf-8")

optimisation = f"""# Optimisation

## Change

Keep the last 128 answers in memory. The key contains the trimmed question, document filter and model name. Restart when the index changes. No answer text is shortened or changed by the cache.

## Before and after

Same 112 questions, same order and model, one request at a time. Model warmup is excluded. The no-cache measurements come from the saved full generation run; the benchmark checks its implementation hash and question IDs before reusing it. Then it runs the same set through an empty cache and repeats it through the populated cache.

{speed_table}

Repeated-workload p95 reduction: **{reduction:.4f}%**. Exact answer agreement with the empty-cache pass: **{same_first}**. Agreement with the independent no-cache pass: **{same_baseline}**. {accuracy_comparison} These are model judgments, not a human accuracy study. Full records are in `eval/results/cache_accuracy.json`.

The 50% latency target is demonstrated for repeated questions already in the cache. It is not established for a real traffic mix. First-use requests still run retrieval and generation. The benchmark does not include internet transit time or concurrent load.

## Chunk choice

On 20 development questions, 120-token chunks with 24-token overlap gave 85% recall@5. Both 180/0 and 180/36 gave 90%. The final choice is 180/0: 3,297 chunks instead of 3,505. Chunk timings are in `eval/results/chunking.json`; they are exploratory local measurements and should not be compared as a controlled service benchmark because other setup work was running.

## Cost model

The local models have **$0 external inference API charges**. Hardware, power and hosting are not free. No API price reduction is claimed.

Let H be a fixed monthly hosting bill and N the number of monthly requests. At the same capacity, hosting cost per request is H/N. At 100 times the traffic it is H/(100N), but only if that machine can actually handle the load. This implementation accepts one active generation request and returns 503 while busy, so that assumption needs a load test.

For a simple arithmetic example, an assumed $20 monthly machine and 1,000 requests give $0.02 per request. At 100,000 requests, the fixed-bill calculation is $0.0002 per request. These are assumptions, not a provider quote or a measured capacity claim. Add electricity and hardware amortisation if using your own machine.

For on-demand hosting billed at C per hour, active compute cost is approximately `C * average_request_seconds / 3600`. Multiply that by request count for monthly active cost, then add idle time, storage and network charges. A cache hit avoids the model call; its savings depend on the actual hit rate. Token counts in the table are workload totals, not dollars.

## Reproduce

```sh
python run.py -m eval.generation --split all
python run.py -m eval.benchmark --split all --baseline eval/results/generation.json
python run.py -m eval.p1_judge
python run.py -m eval.cache_accuracy
```

Run these with other model jobs idle. Check `eval/results/environment.json` for the observed model digests and `requirements-lock.txt` for the tested Windows packages.
"""
(ROOT / "optimisation.md").write_text(optimisation, encoding="utf-8")

sections = [
    ("1. Corpus and users", [
        "The project is a question-answering helper for students reading Python documentation. It uses 25 official Python 3.14.0 reference documents: 209,222 words, about 418 pages at 500 words per page. This is an estimated page count. The cleaned snapshot and source hashes are committed.",
        "The documents are public and covered by the included Python license. No student records are included. The intended users are classmates learning Python; real user feedback and instructor approval have not yet been collected. data/feedback.csv is deliberately blank.",
    ]),
    ("2. Pipeline design", [
        "Offline: extract sections and source anchors, split into 180-token chunks, embed with all-MiniLM-L6-v2, and save JSON plus a NumPy matrix. There are 3,297 chunks. A flat index fits in memory and avoids a database service.",
        "Online: BM25 and vector search each return 30 candidates. Reciprocal rank fusion combines them. A MiniLM cross-encoder reranks the best 20, and Qwen 2.5 7B answers from the best five. A document filter is applied before ranking. Questions are not rewritten.",
        "The model chooses a source number. The app copies the cited passage from the index and links to the original documentation. Missing sources, explicit refusals and low relevance scores return an unknown response. A copied passage may still be interpreted incorrectly.",
        "Chunk-size trial on 20 development questions: 120/24 gave 85% recall@5; 180/0 and 180/36 both gave 90%. The smaller 180/0 index was selected. Long code blocks can still cross chunk boundaries.",
    ]),
    ("3. Retrieval results", [
        "The full set contains 102 drafted answerable questions and 10 out-of-scope questions. Retrieval uses only the 102 answerable items. A hit requires the annotated evidence span from the correct source section among the top five chunks, not just a matching document title.",
        retrieval_table,
        "These are descriptive engineering results, not a sealed holdout. Twenty questions were used for development, and preliminary test results were viewed during implementation. Questions are mostly short API lookups; real student questions may be harder.",
    ]),
    ("4. Generation and Project 1", [
        gen_table,
        "The adapter imports the actual call_json function from BLACK2202/sql-explanation-grader at commit 23473e6. It replaces the SQL rubric with question correctness, support from cited passages and citation relevance. Qwen 2.5 7B judges the saved answers. Raw verdicts and reasons are retained. Known refusal labels override contradictory model judgments.",
        "Model grades are not human labels. Generator and judge use the same model, so shared biases can inflate scores. Token F1 is only word overlap. Exact quote existence is guaranteed by copying evidence and is not a faithfulness result. The human review CSV has empty grading columns and must be reviewed before final submission.",
    ]),
    ("5. Optimisation and cost", [
        speed_table,
        f"The 128-entry cache reduced repeated-workload p95 by {reduction:.4f}%. Exact cached/first-use answer agreement was {same_first}; agreement with the separate no-cache run was {same_baseline}. Identical stored answers preserve their grading. The 50% target is demonstrated for a 100% repeat workload, not for unseen questions or an unknown real hit rate.",
        accuracy_comparison,
        "External inference API charges are $0 because inference is local. Hosting, hardware and electricity still cost money. Fixed monthly hosting cost per request is H/N. At 100x traffic it is H/(100N) only if capacity suffices. An assumed $20/month at 1,000 requests is $0.02/request; at 100,000 it is $0.0002/request before capacity upgrades. These are illustrative assumptions, not provider prices.",
    ]),
    ("6. Limits and remaining work", [
        "Known failures include flattened tables, split code blocks, missed cross-references, nearby APIs outranking the right API, unnecessary refusals and a model misreading real evidence. The postmortem records parsing errors, quote-generation failures and a contradictory judge result found during implementation.",
        "The app was checked in a browser and has 14 automated checks. It runs locally; a public deployment URL has not been provisioned. Deployment instructions are included. Instructor approval, real classmate feedback and human review remain outstanding and are not represented as complete.",
        "The code and draft documentation were prepared with coding-assistant support. The project owner needs to review the implementation and understand it before presenting. explain.md provides a file-by-file reading order and demonstration plan.",
    ]),
]
report_md = "# LibrarianRAG - Project 2 report\n\nCS496 | 26 October 2026\n\n" + "\n\n".join("## " + title + "\n\n" + "\n\n".join(paragraphs) for title, paragraphs in sections)
(ROOT / "report.md").write_text(report_md + "\n", encoding="utf-8")

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="BodySmall", parent=styles["BodyText"], fontName="Helvetica", fontSize=10.2, leading=14, spaceAfter=9))
styles["Heading1"].fontSize = 16
styles["Heading1"].leading = 20
styles["Heading1"].spaceAfter = 12
story = [Paragraph("LibrarianRAG - Project 2", styles["Title"]), Paragraph("CS496 | 26 October 2026", styles["BodySmall"]), Spacer(1, 10)]

def table_from_markdown(text):
    lines = [line for line in text.splitlines() if not line.startswith("| ---")]
    cells = [[Paragraph(escape(cell.strip()), styles["BodySmall"]) for cell in line.strip("|").split("|")] for line in lines]
    widths = [240, 90, 160] if len(cells[0]) == 3 else ([355, 135] if len(cells[0]) == 2 else [160, 75, 75, 90, 90])
    table = Table(cells, colWidths=widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e6eee9")),
        ("LINEBELOW", (0, 0), (-1, 0), .6, colors.HexColor("#93aa9b")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
    ]))
    return table

for i, (title, paragraphs) in enumerate(sections):
    if i in (2, 4):
        story.append(PageBreak())
    story.append(Paragraph(title, styles["Heading1"]))
    for paragraph in paragraphs:
        if paragraph.startswith("| Search") or paragraph.startswith("| Measure") or paragraph.startswith("| Workload"):
            story.extend([table_from_markdown(paragraph), Spacer(1, 12)])
        else:
            story.append(Paragraph(escape(paragraph), styles["BodySmall"]))
    story.append(Spacer(1, 8))

def footer(canvas, doc):
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#59655d"))
    canvas.drawString(50, 28, "LibrarianRAG | Local evaluation; deployment and user study pending")
    canvas.drawRightString(A4[0] - 50, 28, str(doc.page))

pdf = ROOT / "report.pdf"
SimpleDocTemplate(str(pdf), pagesize=A4, rightMargin=50, leftMargin=50, topMargin=40, bottomMargin=45).build(story, onFirstPage=footer, onLaterPages=footer)
OUT.mkdir(exist_ok=True)
copyfile(pdf, OUT / "LibrarianRAG-report.pdf")
print("Updated README.md, optimisation.md, report.md and report.pdf")
