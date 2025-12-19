"""Extract structured numeric and boolean parameters from policy PDFs.

Creates `policies/parameters.json` with extracted parameters for each policy.

Run from project root:
& ".venv/Scripts/python.exe" scripts/extract_policy_parameters.py
"""
import os
import sys
import json
import re
from typing import Dict, Any

ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, ROOT)

from pypdf import PdfReader


def text_to_int(word: str) -> int:
    # very small mapping for common words we expect (e.g., 'twenty')
    mapping = {
        'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
        'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
        'eleven': 11, 'twelve': 12, 'thirteen': 13, 'fourteen': 14,
        'fifteen': 15, 'sixteen': 16, 'seventeen': 17, 'eighteen': 18,
        'nineteen': 19, 'twenty': 20
    }
    return mapping.get(word.lower(), None)


def extract_text_from_pdf(path: str) -> str:
    try:
        reader = PdfReader(path)
        texts = []
        for p in reader.pages:
            t = p.extract_text() or ""
            texts.append(t)
        return "\n".join(texts)
    except Exception as e:
        return f"ERROR: {e}"


def find_percent_of_gdp(text: str) -> Dict[str, Any]:
    # Find patterns like 'below 7 percent of gross domestic product within twenty years'
    out = {}
    # direct percentages
    m = re.search(r'below\s+(\d+(?:\.\d+)?)\s*percent of gross domestic product(?: within (\w+\s+years|\d+\s+years))?', text, re.IGNORECASE)
    if m:
        out['target_health_percent_gdp'] = float(m.group(1))
        when = m.group(2)
        if when:
            # try numeric years
            num = re.search(r'(\d+)', when)
            if num:
                out['target_within_years'] = int(num.group(1))
            else:
                w = when.split()[0]
                i = text_to_int(w)
                if i:
                    out['target_within_years'] = i

    # fiscal surplus percent and year
    m2 = re.search(r'equivalent to\s+([\d\.\-–]+)\s*percent of gross domestic product annually by (\d{4})', text, re.IGNORECASE)
    if m2:
        out['fiscal_surplus_percent_gdp'] = m2.group(1)
        out['fiscal_surplus_target_year'] = int(m2.group(2))

    # more generic search for 'X percent of gross domestic product'
    if 'target_health_percent_gdp' not in out:
        m3 = re.search(r'(\d+(?:\.\d+)?)\s*percent of gross domestic product', text, re.IGNORECASE)
        if m3:
            out['found_percent_of_gdp'] = float(m3.group(1))

    return out


def find_boolean_flags(text: str) -> Dict[str, bool]:
    flags = {}
    flags['zero_out_of_pocket'] = bool(re.search(r'zero[- ]out[- ]of[- ]pocket|zero out of pocket', text, re.IGNORECASE))
    flags['eliminate_medical_bankruptcy'] = bool(re.search(r'eliminate medical bankruptcy|permanently eliminate medical bankruptcy', text, re.IGNORECASE))
    flags['establish_galactic_department_of_health'] = bool(re.search(r'galactic department of health', text, re.IGNORECASE))
    flags['opt_out_voucher_system'] = bool(re.search(r'opt[- ]out|voucher system', text, re.IGNORECASE))
    flags['accelerate_biomedical_innovation'] = bool(re.search(r'biomedical|longevity innovation|innovation boom', text, re.IGNORECASE))
    return flags


def extract_parameters_for_policy(path: str) -> Dict[str, Any]:
    text = extract_text_from_pdf(path)
    if text.startswith('ERROR:'):
        return {'error': text}

    params = {}
    params.update(find_percent_of_gdp(text))
    params.update(find_boolean_flags(text))

    # Extract explicit years mentioned (e.g., 2025, 2040)
    years = sorted({int(y) for y in re.findall(r'\b(20\d{2})\b', text)})
    if years:
        params['years_mentioned'] = years

    # capture short excerpt around target phrases for human review
    excerpt_matches = {}
    for phrase in ['zero out of pocket', 'reduce national health expenditures', 'fiscal surpluses', 'eliminate medical bankruptcy', 'funding mechanisms']:
        i = text.lower().find(phrase)
        if i != -1:
            excerpt_matches[phrase] = text[max(0, i-120):i+300].replace('\n',' ')
    if excerpt_matches:
        params['excerpts'] = excerpt_matches

    return params


def main():
    catalog_path = os.path.join(ROOT, 'policies', 'catalog.json')
    if not os.path.exists(catalog_path):
        print('catalog.json not found. Run scripts/import_policies.py first.')
        return
    with open(catalog_path, 'r', encoding='utf-8') as f:
        catalog = json.load(f)

    results = {}
    # prefer the Galactic Health Act doc
    target = None
    for entry in catalog:
        if 'galactic health act' in entry.get('title','').lower() or 'galactic health' in entry.get('snippet','').lower():
            target = entry
            break
    if not target:
        # fallback: first entry with health keyword
        for entry in catalog:
            if 'health' in entry.get('keywords',[]):
                target = entry
                break

    if not target:
        print('No health policy found in catalog')
        return

    print('Extracting parameters from:', target['title'])
    params = extract_parameters_for_policy(target['source_path'])
    results[target['title']] = params

    out_path = os.path.join(ROOT, 'policies', 'parameters.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print('Wrote parameters to', out_path)


if __name__ == '__main__':
    main()
