#!/usr/bin/env python3
"""
Analyze M4A PDF text to see what funding concepts should be detected
"""

from pathlib import Path
from pypdf import PdfReader
import re

m4a_path = Path("project guidelines/policies and legislation/BILLS-118s1655is.pdf")

if not m4a_path.exists():
    print(f"ERROR: M4A not found at {m4a_path}")
    exit(1)

# Extract text
reader = PdfReader(m4a_path)
text = " ".join([page.extract_text() for page in reader.pages])
print(f"M4A Text size: {len(text):,} characters\n")

# Look for funding-related patterns
print("FUNDING PATTERNS IN M4A TEXT:")
print("=" * 80)

# Tax patterns
patterns = [
    ("payroll tax", r'payroll\s+tax', 3),
    ("income tax", r'income\s+tax', 3),
    ("premium redirect", r'premiums?|insurance\s+contributions', 3),
    ("employer contrib", r'employer\s+contribution|employer\s+paid', 3),
    ("employee contrib", r'employee\s+contribution|employee\s+paid', 3),
    ("excise tax", r'excise\s+tax', 3),
    ("transaction tax", r'(?:financial\s+)?transaction\s+tax|FTT', 3),
    ("tariff", r'tariff', 3),
    ("GDP percentage", r'(\d+(?:\.\d+)?)\s*percent\s+of\s+(?:GDP|gross\s+domestic\s+product)', 1),
]

for name, pattern, context_window in patterns:
    matches = list(re.finditer(pattern, text, re.IGNORECASE))
    print(f"\n{name}: {len(matches)} matches")
    
    if matches:
        # Show first few matches with context
        for i, match in enumerate(matches[:3]):
            start = max(0, match.start() - 100)
            end = min(len(text), match.end() + 100)
            context = text[start:end].replace('\n', ' ')
            print(f"  Match {i+1}: ...{context}...")

print("\n" + "=" * 80)
print("\nSOUTH CAROLINA HEALTHCARE PROVIDER PAYMENT:")
print("=" * 80)

# Look for specific funding mechanism descriptions
if "employer" in text.lower() and "employee" in text.lower():
    print("[+] Mentions employer and employee contributions")

if re.search(r'payroll\s+tax', text, re.IGNORECASE):
    print("[+] Mentions payroll tax")
    
    # Try to find the rate
    payroll_rates = re.findall(r'payroll[^.]*?(\d+(?:\.\d+)?)\s*percent', text, re.IGNORECASE | re.DOTALL)
    if payroll_rates:
        print(f"  Rates found: {payroll_rates}")

if re.search(r'income\s+tax', text, re.IGNORECASE):
    print("[+] Mentions income tax")
    
    # Try to find rates
    income_rates = re.findall(r'income\s+tax[^.]*?(\d+(?:\.\d+)?)\s*percent', text, re.IGNORECASE | re.DOTALL)
    if income_rates:
        print(f"  Rates found: {income_rates}")

print("\n" + "=" * 80)
