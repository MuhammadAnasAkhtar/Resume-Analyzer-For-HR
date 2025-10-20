# src/ats_analyzer.py
import re
from collections import Counter
from textblob import TextBlob
from fuzzywuzzy import process
import logging
from src.utils import extract_emails, extract_phones, contains_generic_phrases

LOG = logging.getLogger("ats_analyzer")

# simple skill bank (extendable); in production use larger curated skills list
DEFAULT_SKILLS = [
    "python","java","sql","javascript","react","node.js","aws","docker","kubernetes",
    "machine learning","nlp","data analysis","excel","project management","sql","GitHub",
    "communication","leadership","problem solving","time management","teamwork","c++","c#","go","ruby","html","css","typescript","angular","vue.js","django","flask","spring","hibernate","rest api","graphql","linux","windows","azure","gcp","ci/cd","jenkins","terraform","ansible","puppet","salesforce","marketing","seo","content creation","social media management" 
]

COMMON_DEGREES = ["bachelor", "master", "phd", "b.sc", "m.sc", "b.s.", "m.s.", "mba"]

def extract_keywords_from_job(job_text, top_n=30):
    words = re.findall(r'\b[a-zA-Z\+#\.\-]{2,}\b', job_text.lower())
    stop = set(["the","and","with","for","using","in","to","of","a","an","as","on","by","or"])
    candidates = [w for w in words if w not in stop and not w.isdigit()]
    counts = Counter(candidates)
    # return most common
    return [w for w,_ in counts.most_common(top_n)]

def keyword_match_score(resume_text, job_keywords):
    resume_words = set(re.findall(r'\b[a-zA-Z\+#\.\-]{2,}\b', resume_text.lower()))
    matched = [k for k in job_keywords if k in resume_words]
    score = int(len(matched) / max(1, len(job_keywords)) * 100)
    return score, matched, [k for k in job_keywords if k not in matched]

def extract_skills(resume_text, skills_bank=None):
    skills_bank = skills_bank or DEFAULT_SKILLS
    text = resume_text.lower()
    found = set()
    for sk in skills_bank:
        if sk in text:
            found.add(sk)
    # fuzzy match for multiword skills
    tokens = re.findall(r'\b[a-zA-Z\+\-\.]{2,}\b', text)
    for sk in skills_bank:
        choice, score = process.extractOne(sk, tokens)
        if score > 90:
            found.add(sk)
    return sorted(list(found))

def years_of_experience(resume_text):
    # naive approach: find date ranges and sum durations; fallback to experience phrases
    years = 0
    dates = re.findall(r'(\b(?:20|19)\d{2})', resume_text)
    try:
        if dates:
            years_in_text = list(map(int, dates))
            if len(years_in_text) >= 2:
                years = max(years_in_text) - min(years_in_text)
            else:
                # look for explicit "X years"
                m = re.search(r'(\d+)\+?\s+years?', resume_text.lower())
                if m:
                    years = int(m.group(1))
    except Exception as e:
        LOG.exception("years_of_experience error: %s", e)
    # clamp
    if years < 0:
        years = 0
    if years == 0:
        # fallback heuristics
        m = re.search(r'(\d+)\s+years?', resume_text.lower())
        if m:
            years = int(m.group(1))
    return years

def detect_education(resume_text):
    lower = resume_text.lower()
    found = []
    for degree in COMMON_DEGREES:
        if degree in lower:
            found.append(degree)
    # try capture universities
    univ = re.findall(r'(university|college|institute|school|academy)[\s,\w\-]{0,60}', resume_text, flags=re.I)
    return {"degrees": list(set(found)), "institutions": univ[:5]}

def format_structure_checks(resume_text, raw_pdf_bytes=None):
    # checks: many ATS break on images/tables; we can't detect images easily after text extraction; check for long lines, tables (many pipes), excessive columns
    checks = []
    # long one-line sections may indicate parsing issues
    lines = resume_text.splitlines()
    avg_line_len = sum(len(l) for l in lines) / max(1, len(lines))
    if avg_line_len > 200:
        checks.append("Long lines detected — possible parsing issues or tables/images causing concatenation.")
    # detect bullets
    bullets = sum(1 for l in lines if re.match(r'^\s*[\*\-\u2022]', l))
    if bullets < 3:
        checks.append("Few bulleted achievements found. Consider using bullets for readability.")
    # detect header sections
    expected_sections = ["experience","education","skills","summary","projects"]
    missing = [s for s in expected_sections if s not in resume_text.lower()]
    if missing:
        checks.append(f"Missing common sections: {', '.join(missing[:3])}.")
    return checks

def contact_info_checks(resume_text):
    emails = extract_emails(resume_text)
    phones = extract_phones(resume_text)
    linkedin = None
    m = re.search(r'(linkedin\.com\/[A-Za-z0-9\-_\/]+)', resume_text, flags=re.I)
    if m:
        linkedin = m.group(1)
    return {"emails": emails, "phones": phones, "linkedin": linkedin}

def readability_scores(resume_text):
    try:
        blob = TextBlob(resume_text)
        # TextBlob doesn't give Flesch; approximate with sentence/word measures
        words = len(blob.words)
        sentences = max(1, len(blob.sentences))
        avg_words = words / sentences
        # simple readability proxy: higher average words per sentence -> harder
        fk_est = max(0, 206.835 - 1.015 * avg_words - 84.6 * (sum(len(w) for w in blob.words) / max(1, words))/words)
    except Exception:
        fk_est = None
    return {"avg_words_per_sentence": avg_words, "flesch_estimate": int(fk_est) if fk_est else None}

def detect_achievements(resume_text):
    # find lines with % or numbers + keywords like increased, reduced, saved, grew
    lines = resume_text.splitlines()
    achievements = []
    for l in lines:
        if re.search(r'(\d+%|\$\d+|\d+\s+%|\bincreased\b|\breduced\b|\bsaved\b|\bgrew\b)', l.lower()):
            achievements.append(l.strip())
    return achievements[:20]

def relevance_score(keyword_score, skills_count, achievements_count, years):
    # weighted combination -> 0..100
    ks = keyword_score
    sc = min(30, skills_count * 5)  # up to 30
    ac = min(20, achievements_count * 4)  # up to 20
    ye = min(20, years * 2)  # up to 20
    base = ks * 0.5 + sc + ac + ye
    score = int(min(100, base))
    return score

def detect_action_verb_weakness(resume_text):
    weak_verbs = ["helped", "worked on", "responsible for", "assisted", "involved in"]
    found = []
    for v in weak_verbs:
        if v in resume_text.lower():
            found.append(v)
    return found

def generic_phrase_detector(resume_text):
    return contains_generic_phrases(resume_text)
