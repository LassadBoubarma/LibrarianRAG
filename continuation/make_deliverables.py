"""Write plain-language reports from saved results, including unfinished measurements.

Run: python continuation/make_deliverables.py
Requires reportlab only for the PDF. It never runs a model or invents missing scores.
"""
import json
import sys
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (KeepTogether, PageBreak, Paragraph, SimpleDocTemplate,
                                Spacer, Table, TableStyle)

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "eval/results"
sys.path.insert(0, str(ROOT))
from eval.common import metadata  # noqa: E402


def saved(filename):
    path = RESULTS / filename
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def pct(value):
    return "not measured" if value is None else f"{100 * value:.1f}%"


def md_table(headers, rows):
    return "| " + " | ".join(headers) + " |\n| " + " | ".join("---" for _ in headers) + " |\n" + "\n".join("| " + " | ".join(str(c) for c in row) + " |" for row in rows)


def html(text):
    return escape(str(text).replace("**", "").replace("`", "")).replace("\n", " ")


ablations = saved("ablation.json")
gen = saved("generation.json")
judge = saved("p1_judge.json")
benchmark = saved("benchmark.json")
assert gen and len(gen["rows"]) == 112, "Expected complete saved generation data"
assert ablations and len(ablations) == 4, "Expected four retrieval ablations"
summary = gen["summary"]
old_code = gen["metadata"] != metadata()

# Only report a complete, matching Project 1 run. The five-question trial is excluded.
valid_judge = bool(judge and judge.get("summary", {}).get("questions") == 112
                   and judge["summary"].get("errors") == 0
                   and judge.get("generation_sha256") is not None)
if valid_judge:
    import hashlib
    valid_judge = judge["generation_sha256"] == hashlib.sha256((RESULTS / "generation.json").read_bytes()).hexdigest()
valid_benchmark = bool(benchmark and benchmark.get("questions") == 112
                       and benchmark.get("metadata") == gen["metadata"]
                       and benchmark.get("split") == "all")

retrieval_rows = [(x["mode"], pct(x["recall_at_k"]), f'{x["p50_ms"]:.1f} ms', f'{x["p95_ms"]:.1f} ms') for x in ablations]
retrieval = md_table(["Search", "Recall@5", "p50 search", "p95 search"], retrieval_rows)
generation_rows = [
    ("Answer coverage, 102 answerable", pct(summary["answer_coverage"])),
    ("Refusal, 10 out-of-scope", pct(summary["abstention_accuracy_unanswerable"])),
    ("Gold-evidence citation, 102 answerable", pct(summary["gold_citation_rate_all_answerable"])),
    ("Copied quote exists, answered responses", pct(summary["exact_quote_rate_answered"])),
    ("Token overlap F1, not semantic correctness", f'{summary["answer_token_f1"]:.3f}'),
    ("End-to-end p50, saved run", f'{summary["p50_ms"]:.1f} ms'),
    ("End-to-end p95, saved run", f'{summary["p95_ms"]:.1f} ms'),
]
if valid_judge:
    j = judge["summary"]
    generation_rows += [
        ("P1 model-judged correctness, all 112", pct(j["model_judged_correctness"])),
        ("P1 model-judged faithfulness, answered", pct(j["model_judged_faithfulness_answered"])),
        ("P1 model-judged citation support, answered", pct(j["model_judged_citation_support_answered"])),
    ]
else:
    generation_rows.append(("P1 correctness / faithfulness, all 112", "not measured"))
generation = md_table(["Measure", "Saved result"], generation_rows)

if valid_benchmark:
    b = benchmark["results"]
    speed_rows = [(label, f'{b[key]["p50_ms"]:.3f}', f'{b[key]["p95_ms"]:.3f}',
                   str(b[key]["cache_hits"])) for key, label in [
                       ("baseline_no_cache", "No cache"), ("cache_first_use", "First-use cache"),
                       ("cache_repeated", "Repeated cache")]]
    speed = md_table(["Workload", "p50 ms", "p95 ms", "Cache hits"], speed_rows)
    speed_result = (f'In the measured 100% repeated-question workload, p95 fell by '
                    f'{b["p95_reduction_percent_repeated_only"]:.1f}%. '
                    f'Repeated answers exactly matched first-use answers in '
                    f'{pct(b["same_answer_rate_vs_first_use"])} of cases. '
                    'This does not measure the hit rate of real users.')
else:
    speed = 'Cache first-use and repeat p50/p95: **not measured**. `benchmark.json` does not exist.'
    speed_result = 'No 50% p95 reduction has been demonstrated by a completed benchmark.'

result_time = '19 October 2026, Windows 3.11, Ryzen 5 5600X, RTX 3060'
version_note = ('The saved answers were produced before the latest code fixes; rerun generation for updated scores.'
                if old_code else 'These generation records match the code hash in this checkout.')

readme_path = ROOT / "README.md"
readme = readme_path.read_text(encoding="utf-8")
start = readme.index('## Results\n') + len('## Results\n')
end = readme.index('\n## Evaluation', start)
readme_results = f"""
These are saved results from {result_time}. {version_note} The development questions are included; this is not a blind test.

{retrieval}

{generation}

**Correctness and faithfulness need the full Project 1 judge and human review.** Quote existence (100%) only means the evidence text was copied from a document. It does not show that the answer is correct. See [quality_review.md](quality_review.md) for concrete mistakes.

**Cache benchmark:** {speed_result} The benchmark is resumable and must be run with Ollama available.
"""
readme_path.write_text(readme[:start] + readme_results + readme[end:], encoding='utf-8')

optimisation = f"""# Optimisation

## What changed

The service stores up to 128 question answers in a small in-memory cache. A hit avoids retrieval, reranking and the Ollama call. The cache key includes the exact question, selected document and model. Restart the server when changing documents or model versions. The app is otherwise a simple, single-worker generator.

## Before and after

The complete generation run on {result_time} measured **p50 {summary['p50_ms']:.1f} ms** and **p95 {summary['p95_ms']:.1f} ms** without cached responses. It contains 112 sequential questions. The cache benchmark was interrupted before completion. No completed paired before/after latency comparison is supplied.

{speed}

{speed_result} A full cache has no effect on first-time questions. Even after completing the benchmark, the all-repeat result must not be presented as the expected speedup for normal traffic. A real cache-hit percentage and mixed workload would need to be measured with users.

The code now saves `eval/results/benchmark_progress.json` after each question, so an interrupted benchmark can resume without losing the completed calls. The progress file is temporary and is not a result.

## Smaller index

On 20 development questions, reranked recall@5 was **85%** with 120 tokens/24 overlap, **90%** with 180/0 and **90%** with 180/36. The selected 180/0 index has 3,297 chunks, compared with 3,505 for 180/36. This is an index-size choice, not a demonstrated 50% latency reduction. Timings in `chunking.json` were exploratory, not controlled service timings.

## Cost per request and 100x

There is **no external inference API fee** because the models run on Ollama. Computer time, hardware, electricity, bandwidth and hosting still cost money. With an assumed fixed monthly hosting bill H and N requests, the simple per-request hosting figure is H/N. For a hypothetical $20/month and 1,000 monthly requests, that is $0.020/request; at 100,000 it is $0.00020/request **only if the same machine has enough capacity**. Neither $20 nor that capacity has been observed or quoted from a provider.

At an hourly active compute price C, active compute cost for one request is roughly `C * (request seconds / 3600)`, plus idle time and other charges. The app serialises model calls and returns 503 when busy. It has not been load-tested at 100x; do not assume the fixed-cost example can be achieved.

## Complete the benchmark locally

Run after installing Python 3.11/3.12, dependencies and Ollama. Keep other GPU work idle. The new code must be used for **both** the baseline and the repeated run:

```sh
python run.py -m eval.generation --split all
python run.py -m eval.benchmark --split all --baseline eval/results/generation.json
python .venv/bin/python continuation/make_deliverables.py
```

On Windows replace the last command with `.venv\\Scripts\\python continuation/make_deliverables.py`. Save the resulting `benchmark.json` and check its environment metadata. If the run stops, repeat the benchmark command. The benchmark uses all 112 questions, one request at a time, and separates no-cache, empty-cache and already-cached requests. It does not measure external network time or concurrent users.
"""
(ROOT / 'optimisation.md').write_text(optimisation, encoding='utf-8')

sections = [
('1. Corpus and users', [
 'This is a question-answering helper for students who consult the Python standard-library documentation. The corpus is 25 official Python 3.14.0 pages, containing 209,222 extracted words (about 418 equivalent pages at 500 words per page, not an actual PDF page count). The cleaned documents, original links, anchors and license are included in the repository.',
 'There are 102 drafted, source-linked answerable questions and 10 out-of-scope questions. These are engineering test questions, not questions collected from real users. Students are the intended users, but instructor approval and anonymous classmate feedback are still pending.'
]),
('2. Pipeline', [
 'The offline code extracts named sections, keeps each source URL, splits text into 180-token chunks with no overlap and embeds them with all-MiniLM-L6-v2. The shipped index data is 3,297 chunks. A NumPy matrix and JSON metadata are sufficient at this size; a separate vector database would add setup work.',
 'For each question BM25 and vector search collect 30 results apiece. Reciprocal rank fusion combines the lists, a MiniLM cross-encoder reranks 20 candidates, and the five best passages go to Qwen 2.5 3B through Ollama. A document selector filters results. The app does not rewrite follow-up questions.',
 'The model returns an answer and a passage number. The server copies the passage from its index instead of accepting a model-written quote. It refuses low-relevance or invalid-source answers. A copied quote is not proof that the claim follows from that quote. Recent small code fixes tighten input handling, refusals and named-API citations but have not yet been reevaluated.'
]),
('3. Retrieval results', [
 'Saved 19 October 2026 ablation on all 102 answerable questions. A hit requires the annotated evidence span in the top five, not just a matching page. Times are local search-step milliseconds.',
 retrieval,
 'Reranking improves recall from hybrid 84.3% to 91.2%, at a large search-latency cost. This is a descriptive test set; 20 questions were used in development and the final set was not kept sealed.'
]),
('4. Generation and checking', [
 'Saved 19 October 2026 run of 112 questions (the answer-generating code has since changed):',
 generation,
 'There were 95 answered items in the saved run: 95 of 102 answerable questions were answered and all 10 out-of-scope questions were refused. A 100% copied-quote rate does not establish faithfulness; the gold passage was cited on only 65.7% of answerable questions. The token F1 of 0.314 measures overlap of words, not answer quality.',
 'The full Project 1 correctness/faithfulness/citation judging on all 112 current saved answers has not been run. The only existing five-question judge file belongs to a different development version and is excluded. Human grading columns remain blank. Examples of actual wrong answers appear in quality_review.md; no model-judge percentages are invented.' if not valid_judge else 'The complete Project 1 grading uses the pinned SQL-grader model-calling helper but a RAG-specific rubric. Those are model judgments, not human grades; individual reasons and source passages remain available for review.'
]),
('5. Week 8 and cost', [
 f'The cache holds 128 exact-question responses. {speed_result}',
 speed,
 'A chunking trial on 20 development questions gave recall@5 85% at 120/24, and 90% at both 180/0 and 180/36. The chosen 180/0 index is smaller, but this does not prove the assigned 50% end-to-end optimisation target.',
 'Local inference incurs no external per-token API fee, but machines, electricity and hosting cost money. For a purely hypothetical fixed $20/month host: 1,000 requests cost $0.020/request, and 100,000 cost $0.00020/request only if capacity is sufficient. This is a cost illustration, not a host quote or load measurement. The app permits one active model call and returns HTTP 503 for simultaneous requests.'
]),
('6. Failures and remaining work', [
 'Observed mistakes include saying that all([]) returns a start value, naming zip() instead of itertools.chain, mixing up csv.writer and DictWriter, and giving the wrong sorted insertion function. Long code blocks, flattened tables, cross-references and ambiguous names remain difficult. Some questions are refused despite having an answer; some cited passages do not support the actual claim.',
 'The project has a local browser preview and nine earlier automated checks recorded in its notes. In this environment, offline data integrity checks and four new tests passed; the full dependency-based test suite and updated model run are not verified. No public URL, instructor approval, classmate study or human grades are available.',
 'Documentation and code were prepared with coding-assistant support. The owner should read explain.md, review the code and actual scores, obtain approval and genuine user feedback, and complete the live judge, benchmark and deployment before claiming those requirements are met.'
])]
report_text = '# LibrarianRAG - Project 2 report\n\nCS496 | 26 October 2026\n\n' + '\n\n'.join('## ' + title + '\n\n' + '\n\n'.join(parts) for title, parts in sections) + '\n'
(ROOT / 'report.md').write_text(report_text, encoding='utf-8')

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='Body10', parent=styles['BodyText'], fontName='Helvetica', fontSize=9.6, leading=13.6, spaceAfter=8))
styles.add(ParagraphStyle(name='Section14', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=13.2, leading=17, spaceBefore=7, spaceAfter=8, textColor=colors.HexColor('#173b4a')))
styles['Title'].fontSize = 19
styles['Title'].leading = 24
styles.add(ParagraphStyle(name='SmallTable', parent=styles['BodyText'], fontName='Helvetica', fontSize=8.4, leading=10.8))

story = [Paragraph('LibrarianRAG | Project 2', styles['Title']),
         Paragraph('CS496  |  26 October 2026  |  Measured and unmeasured results kept separate', styles['Body10']), Spacer(1, 6)]


def pdf_table(markdown):
    lines = [r for r in markdown.splitlines() if r.startswith('| ') and not r.startswith('| ---')]
    if not lines:
        return Paragraph(html(markdown), styles['Body10'])
    values = [[Paragraph(html(x.strip()), styles['SmallTable']) for x in r.strip('|').split('|')] for r in lines]
    count = len(values[0])
    if count == 4:
        widths = [165, 110, 105, 105]
    elif count == 2:
        widths = [345, 140]
    else:
        widths = [485 / count] * count
    table = Table(values, colWidths=widths, hAlign='LEFT', repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e8f0f2')),
        ('LINEBELOW', (0, 0), (-1, 0), 0.6, colors.HexColor('#8eaaaa')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f6f8f9')]),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 7), ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 5), ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    return table


for n, (title, paragraphs) in enumerate(sections):
    if n in (2, 4):
        story.append(PageBreak())
    story.append(Paragraph(html(title), styles['Section14']))
    for paragraph in paragraphs:
        if paragraph.startswith('| '):
            story.extend([pdf_table(paragraph), Spacer(1, 9)])
        else:
            story.append(Paragraph(html(paragraph), styles['Body10']))


def footer(canvas, doc):
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(colors.HexColor('#66777a'))
    canvas.drawString(52, 30, 'LibrarianRAG  |  Evidence from saved local experiments; missing runs not inferred')
    canvas.drawRightString(A4[0] - 52, 30, str(doc.page))

pdf = ROOT / 'report.pdf'
SimpleDocTemplate(str(pdf), pagesize=A4, rightMargin=54, leftMargin=54,
                  topMargin=45, bottomMargin=48).build(story, onFirstPage=footer, onLaterPages=footer)
print(f'Wrote README.md, optimisation.md, report.md and report.pdf (full P1 judge: {valid_judge}; full cache benchmark: {valid_benchmark})')
