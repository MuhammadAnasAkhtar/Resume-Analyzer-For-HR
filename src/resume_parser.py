# src/resume_parser.py
import pdfplumber
from typing import IO
import re

def extract_text_from_pdf(pdf_file: IO) -> str:
    text = ""
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    # Normalize whitespace
    text = re.sub(r'\n{2,}', '\n\n', text)
    return text.strip()
