"""Scan `project guidelines/policies and legislation` and build a simple JSON catalog.

Runable script: from project root run
& ".venv/Scripts/python.exe" scripts/import_policies.py
"""
import os
import sys
import json
from pypdf import PdfReader

ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, ROOT)
from core.policies import Policy

INPUT_DIR = os.path.join(ROOT, "project guidelines", "policies and legislation")
OUT_DIR = os.path.join(ROOT, "policies")
os.makedirs(OUT_DIR, exist_ok=True)

KEYWORDS = ['health', 'act', 'amend', 'section', 'article', 'revenue', 'spending', 'debt', 'erpo', 'screen', 'legis', 'clause']


def extract_first_page_snippet(path: str) -> (int, str):
    try:
        reader = PdfReader(path)
        pages = len(reader.pages)
        text = ""
        if pages > 0:
            text = reader.pages[0].extract_text() or ""
        snippet = " ".join(text.split())[:2000]
        return pages, snippet
    except Exception as e:
        return 0, f"ERROR: {e}"


def build_catalog():
    catalog = []
    if not os.path.isdir(INPUT_DIR):
        print(f"Input directory does not exist: {INPUT_DIR}")
        return
    for fname in sorted(os.listdir(INPUT_DIR)):
        if not fname.lower().endswith('.pdf'):
            continue
        path = os.path.join(INPUT_DIR, fname)
        pages, snippet = extract_first_page_snippet(path)
        kws = [k for k in KEYWORDS if k in (snippet + fname).lower()]
        policy = Policy.from_pdf(path=path, title=fname, keywords=kws, snippet=snippet, pages=pages)
        catalog.append(policy.to_dict())

    out_path = os.path.join(OUT_DIR, 'catalog.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)
    print(f"Wrote {len(catalog)} policies to {out_path}")


if __name__ == '__main__':
    build_catalog()
