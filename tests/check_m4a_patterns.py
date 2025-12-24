import sys
sys.path.insert(0, '/e:/AI Projects/polisim')

from pathlib import Path
from core.pdf_policy_parser import PolicyPDFProcessor
import re

processor = PolicyPDFProcessor()
text = processor.extract_text_from_pdf(Path('project guidelines/policies and legislation/BILLS-118s1655is.pdf'))

print('Searching M4A text for funding patterns...\n')

# Count patterns
payroll = len(re.findall(r'payroll', text, re.IGNORECASE))
employer_contrib = len(re.findall(r'employer.*contribution', text, re.IGNORECASE | re.DOTALL))
employee_contrib = len(re.findall(r'employee.*contribution', text, re.IGNORECASE | re.DOTALL))
income_tax = len(re.findall(r'income\s+tax', text, re.IGNORECASE))

print(f"Payroll mentions: {payroll}")
print(f"Employer contribution: {employer_contrib}")
print(f"Employee contribution: {employee_contrib}")
print(f"Income tax: {income_tax}\n")

# Show examples
print("Example payroll excerpts:")
for match in re.finditer(r'.{0,40}payroll.{0,40}', text, re.IGNORECASE):
    print(f"  ...{match.group(0)[:100]}...")
    break

print("\nExample employer contribution excerpts:")
for match in re.finditer(r'.{0,30}employer.{0,30}contribution.{0,30}', text, re.IGNORECASE | re.DOTALL):
    excerpt = match.group(0).replace('\n', ' ')
    print(f"  ...{excerpt[:100]}...")
    break
