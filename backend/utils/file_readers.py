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
    try:
        doc = Document(path)
        text = ""
        for para in doc.paragraphs:
            text += para.text + "\n"
        return text
    except Exception:
        # Fallback for malformed docx files that crash python-docx
        import zipfile
        import xml.etree.ElementTree as ET
        try:
            text = ""
            with zipfile.ZipFile(path) as z:
                xml_content = z.read('word/document.xml')
                tree = ET.fromstring(xml_content)
                # Extract all text nodes
                for node in tree.iter():
                    if node.tag.endswith('}t') and node.text:
                        text += node.text + " "
            return text
        except Exception:
            return ""

def read_excel(path):
    df = pd.read_excel(path)
    return df.to_string()
