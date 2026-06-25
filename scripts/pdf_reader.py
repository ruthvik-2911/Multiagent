import os
from pypdf import PdfReader

pdf_path = r"data\Contracts\HISTORY-ENGLISH.pdf"

reader = PdfReader(pdf_path)

text = ""

for page_num, page in enumerate(reader.pages):
    page_text = page.extract_text()

    if page_text:
        text += page_text

print("\n")
print("=" * 80)
print("PDF SUCCESSFULLY READ")
print("=" * 80)

print(f"Total Pages : {len(reader.pages)}")
print(f"Total Characters : {len(text)}")

print("=" * 80)
print(text[:2000])
print("=" * 80)