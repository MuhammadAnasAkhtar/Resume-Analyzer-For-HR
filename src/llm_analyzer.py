# src/llm_analyzer.py
from openai import OpenAI
from src.config import openai_client
import textwrap
import json
import logging
import requests
from bs4 import BeautifulSoup

LOG = logging.getLogger("llm_analyzer")


def analyze_resume_via_llm(resume_text: str, job_text: str):
    prompt = textwrap.dedent(f"""
    You are an expert HR analyst. Compare the resume to the job description.

    Return strictly valid JSON with keys:
    - strengths: array of short strings
    - missing_skills: array of short strings
    - fit_score: integer 0-100
    - quick_recommendation: short string
    - tone: one-word label (e.g., "leadership", "technical", "collaborative")
    - suggested_roles: array of {{"role": "Role Name", "confidence": percent_int}}

    Resume:
    {resume_text[:4000]}

    Job Description:
    {job_text[:4000]}

    Return only JSON.
    """)
    resp = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": "You are an expert HR analyst."},
                  {"role": "user", "content": prompt}],
        max_tokens=800
    )
    text = resp.choices[0].message.content
    try:
        return json.loads(text)
    except Exception:
        # attempt lightweight extraction of lists as fallback
        LOG.exception("LLM returned non-JSON; returning raw but trying to extract bullets.")
        # Build a safer structure with raw content
        return {"raw": text}


def rewrite_achievement(bullet_text: str, target_style="quantified"):
    prompt = textwrap.dedent(f"""
    Rewrite the following resume bullet to be more {target_style}, concise and achievement-focused.
    Return only the rewritten bullet as plain text.

    Bullet:
    {bullet_text}
    """)
    resp = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": "You are a resume-writing expert."},
                  {"role": "user", "content": prompt}],
        max_tokens=150
    )
    return resp.choices[0].message.content.strip()


def full_resume_rewrite(resume_text: str, job_text: str, tone="leadership"):
    prompt = textwrap.dedent(f"""
    You are an expert resume writer. Rewrite the resume below to optimize for the job description provided.
    - Use measurable achievements where possible.
    - Use action verbs.
    - Keep similar length but more focused.
    - Output as plain text resume.

    Tone: {tone}

    Job:
    {job_text[:2000]}

    Resume:
    {resume_text[:4000]}
    """)
    resp = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": "You are an expert resume writer."},
                  {"role": "user", "content": prompt}],
        max_tokens=1200
    )
    return resp.choices[0].message.content


def generate_linkedin_summary(resume_text: str):
    prompt = textwrap.dedent(f"""
    Convert this resume into an optimized LinkedIn headline and summary (1-2 sentence headline, 3-4 short bullet summary lines).
    Return JSON: {{ "headline": "...", "summary_bullets": ["...", "..."] }}
    Resume:
    {resume_text[:3000]}
    """)
    resp = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": "You are an expert LinkedIn optimizer."},
                  {"role": "user", "content": prompt}],
        max_tokens=300
    )
    try:
        return json.loads(resp.choices[0].message.content)
    except Exception:
        return {"raw": resp.choices[0].message.content}


def analyze_linkedin_profile(linkedin_url: str):
    """
    Try to fetch a public LinkedIn profile page and extract basic text for LLM analysis.
    LinkedIn may block scraping; if so, this will return an error and user can paste profile text instead.
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/115.0 Safari/537.36"
        }
        r = requests.get(linkedin_url, headers=headers, timeout=10)
        if r.status_code != 200:
            return {"error": f"LinkedIn returned status {r.status_code}. LinkedIn often blocks automated fetches. Try pasting profile text instead."}
        soup = BeautifulSoup(r.text, "html.parser")
        # Best-effort extracts
        headline = ""
        about_text = ""
        h1 = soup.find("h1")
        if h1:
            headline = h1.get_text(separator=" ", strip=True)
        # 'About' section might be in a <section id="about"> or class-based; try multiple
        about = soup.find(lambda tag: tag.name in ["section", "div"] and "about" in (tag.get("id") or "").lower())
        if about:
            about_text = about.get_text(separator=" ", strip=True)
        # fallback: gather long text blocks
        if not about_text:
            ps = soup.find_all("p")
            long_ps = [p.get_text(strip=True) for p in ps if len(p.get_text(strip=True)) > 80]
            about_text = "\n".join(long_ps[:3])
        # ask LLM to analyze headline/about
        prompt = textwrap.dedent(f"""
        You are an expert HR analyst. Review this LinkedIn profile info and return JSON:
        - strengths: array of short strings
        - missing_skills: array of short strings
        - quick_recommendation: short string

        Headline: {headline}
        About: {about_text}
        Return only JSON.
        """)
        resp = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": "You are an expert HR analyst."},
                      {"role": "user", "content": prompt}],
            max_tokens=400
        )
        try:
            return json.loads(resp.choices[0].message.content)
        except Exception:
            return {"raw": resp.choices[0].message.content}
    except Exception as e:
        LOG.exception("LinkedIn fetch exception: %s", e)
        return {"error": "LinkedIn fetch failed. LinkedIn often blocks scrapers; paste the profile text if possible."}
