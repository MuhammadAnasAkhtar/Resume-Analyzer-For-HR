# src/utils.py
import os
import re

COMMON_GENERIC_PHRASES = [
    "hardworking", "team player", "results-driven", "detail-oriented",
    "excellent communication skills", "responsible for", "experienced in"
]

def list_files_in_folder(folder_path):
    return [f for f in os.listdir(folder_path) if not f.startswith('.') and os.path.isfile(os.path.join(folder_path, f))]

def extract_emails(text):
    return re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)

def extract_phones(text):
    return re.findall(r"(\+?\d[\d\-\s]{7,}\d)", text)

def contains_generic_phrases(text):
    found = []
    ltext = text.lower()
    for p in COMMON_GENERIC_PHRASES:
        if p in ltext:
            found.append(p)
    return found
