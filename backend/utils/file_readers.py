import pandas as pd
from pypdf import PdfReader
from docx import Document

def read_pdf(path):
    reader = PdfReader(path)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text

def read_docx(path):
    doc = Document(path)
    text = ""
    for para in doc.paragraphs:
        text += para.text + "\n"
    return text

def read_excel(path):
    df = pd.read_excel(path)
    return df.to_string()
