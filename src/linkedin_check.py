import re

def check_linkedin(resume_text: str):
    linkedin_url = re.search(r"(https?://(www\.)?linkedin\.com/[^\s]+)", resume_text, re.IGNORECASE)
    if linkedin_url:
        return {
            "status": "Found ✅",
            "url": linkedin_url.group(1),
            "feedback": "LinkedIn profile detected. Ensure it’s updated and matches your resume."
        }
    else:
        return {
            "status": "Missing ⚠️",
            "url": None,
            "feedback": "No LinkedIn profile found. Add one to improve professional credibility."
        }
