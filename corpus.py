"""Download a fixed Python release and keep its text and source locations."""
import hashlib
import json
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

from settings import DATA

BASE = "https://docs.python.org/release/3.14.0/"
MODULES = "functions stdtypes exceptions pathlib collections json csv datetime re itertools functools os shutil math statistics random string argparse logging unittest typing dataclasses sqlite3 heapq bisect".split()


def extract(html, document):
    soup = BeautifulSoup(html, "html.parser")
    main = soup.select_one('div.body')
    if main is None:
        raise ValueError(f"No document body in {document}")
    for link in main.select("a.headerlink"):
        link.decompose()
    title = main.find("h1").get_text(" ", strip=True)
    sections = {}
    # A paragraph belongs to its nearest function definition or section heading.
    for block in main.find_all(["p", "pre", "tr"]):
        if block.find_parent(["pre", "tr"]):
            continue
        parent = block.find_parent("dd")
        definitions = parent.find_previous_siblings("dt") if parent else []
        definition = definitions[-1] if definitions else None
        section = block.find_parent("section")
        anchor = (definition.get("id") if definition else None)
        anchor = anchor or (section.get("id") if section else "top") or "top"
        heading = definition if definition else (section.find(["h1", "h2", "h3", "h4"]) if section else None)
        text = block.get_text("" if block.name == "pre" else " ", strip=block.name != "pre")
        if block.name != "pre":
            text = " ".join(text.split())
        if not text.strip():
            continue
        record = sections.setdefault(anchor, {
            "id": f"{document}#{anchor}", "document": document,
            "title": title, "section": heading.get_text(" ", strip=True) if heading else title,
            "url": BASE + f"library/{document}.html#{anchor}",
            "version": "3.14.0", "author": "Python documentation contributors",
            "release_date": "2025-10-07", "text": "",
        })
        record["text"] += text + "\n\n"
    return list(sections.values())


def main():
    raw = DATA / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    records, hashes = [], {}
    session = requests.Session()
    session.headers["User-Agent"] = "LibrarianRAG student project (one-time documentation download)"
    for name in MODULES:
        path = raw / f"{name}.html"
        if not path.exists():
            response = session.get(BASE + f"library/{name}.html", timeout=60)
            response.raise_for_status()
            path.write_bytes(response.content)
        html = path.read_bytes()
        hashes[name] = hashlib.sha256(html).hexdigest()
        records.extend(extract(html, name))
        print(f"Read {name}", flush=True)
    output = DATA / "documents.jsonl"
    output.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records), encoding="utf-8")
    license_response = session.get(BASE + "license.html", timeout=60)
    license_response.raise_for_status()
    license_soup = BeautifulSoup(license_response.content, "html.parser")
    (DATA / "PYTHON-LICENSE.txt").write_text(license_soup.select_one("div.body").get_text("\n", strip=True), encoding="utf-8")
    words = sum(len(r["text"].split()) for r in records)
    manifest = {"base_url": BASE, "downloaded_at": datetime.now(timezone.utc).isoformat(),
                "documents": len(MODULES), "sections": len(records), "words": words,
                "estimated_pages_at_500_words": round(words / 500, 1),
                "sha256": hashes, "corpus_sha256": hashlib.sha256(output.read_bytes()).hexdigest()}
    (DATA / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in manifest.items() if k != "sha256"}, indent=2))


if __name__ == "__main__":
    main()
