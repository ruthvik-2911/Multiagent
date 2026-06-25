from docx import Document

doc_path = r"data\Policies\Policy.docx"

doc = Document(doc_path)

text = ""

for para in doc.paragraphs:
    text += para.text + "\n"

print("=" * 50)
print("DOCX CONTENT")
print("=" * 50)
print(text)
