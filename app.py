# app.py
import os
import uuid
import json
import logging
from flask import (
    Flask, render_template, request, redirect, url_for, flash,
    send_file, jsonify
)
from werkzeug.utils import safe_join

from werkzeug.utils import secure_filename

from src.resume_parser import extract_text_from_pdf
from src.ats_analyzer import (
    extract_keywords_from_job, keyword_match_score, extract_skills,
    years_of_experience, detect_education, format_structure_checks,
    contact_info_checks, readability_scores, detect_achievements,
    relevance_score, detect_action_verb_weakness, generic_phrase_detector
)
from src.llm_analyzer import (
    analyze_resume_via_llm, rewrite_achievement, full_resume_rewrite,
    generate_linkedin_summary, analyze_linkedin_profile
)
from src.embeddings import store_embedding
from src.matcher import find_best_match

UPLOAD_FOLDER = "data/uploads"
ALLOWED_EXTENSIONS = {"pdf"}
MAX_RESUMES = 20

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "super-secret-key")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50 MB

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger("app")


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    # Multiple resume files
    job_title = request.form.get('job_title')

    resume_files = request.files.getlist("resume")
    job_file = request.files.get("job")
    linkedin_url = request.form.get("linkedin_url", "").strip()
    top_n = int(request.form.get("top_n", 1))

    if not resume_files or len(resume_files) == 0:
        flash("Please upload at least one resume PDF.")
        return redirect(url_for("home"))

    if len(resume_files) > MAX_RESUMES:
        flash(f"Please upload at most {MAX_RESUMES} resumes.")
        return redirect(url_for("home"))

    if not job_file:
        flash("Please upload a job description PDF.")
        return redirect(url_for("home"))

    if not allowed_file(job_file.filename):
        flash("Job description must be a PDF.")
        return redirect(url_for("home"))

    # Save job file
    job_filename_orig = secure_filename(job_file.filename)
    job_saved_name = f"{uuid.uuid4()}_{job_filename_orig}"
    job_path = os.path.join(app.config["UPLOAD_FOLDER"], job_saved_name)
    job_file.save(job_path)
    with open(job_path, "rb") as jf:
        job_text = extract_text_from_pdf(jf)

    # LinkedIn analysis (best-effort)
    linkedin_analysis = None
    if linkedin_url:
        try:
            linkedin_analysis = analyze_linkedin_profile(linkedin_url)
        except Exception as e:
            LOG.exception("LinkedIn analysis error: %s", e)
            linkedin_analysis = {"error": "LinkedIn fetch/analysis failed. Try pasting profile text."}

    # Process each resume, compute scores and LLM analysis
    all_results = []
    for f in resume_files:
        if not f or f.filename == "":
            continue
        if not allowed_file(f.filename):
            continue

        orig_name = secure_filename(f.filename)
        saved_name = f"{uuid.uuid4()}_{orig_name}"
        saved_path = os.path.join(app.config["UPLOAD_FOLDER"], saved_name)
        f.save(saved_path)

        # Extract text
        with open(saved_path, "rb") as rf:
            resume_text = extract_text_from_pdf(rf)

        # store embedding best-effort
        try:
            store_embedding(str(uuid.uuid4()), (resume_text[:2000] or " "), {"filename": orig_name})
        except Exception:
            LOG.exception("Embedding store failed; continuing.")

        # ATS core features
        job_kws = extract_keywords_from_job(job_text, top_n=40)
        kw_score, matched_kws, missing_kws = keyword_match_score(resume_text, job_kws)
        skills_found = extract_skills(resume_text)
        yrs = years_of_experience(resume_text)
        edu = detect_education(resume_text)
        format_checks = format_structure_checks(resume_text)
        contact = contact_info_checks(resume_text)
        readability = readability_scores(resume_text)
        achievements = detect_achievements(resume_text)
        generic_phrases = generic_phrase_detector(resume_text)
        weak_verbs = detect_action_verb_weakness(resume_text)
        rel_score = relevance_score(kw_score, len(skills_found), len(achievements), yrs)

        # LLM analysis (best-effort, may be non-JSON fallback)
        try:
            llm_analysis = analyze_resume_via_llm(resume_text, job_text)
        except Exception:
            LOG.exception("LLM analysis failed for file: %s", orig_name)
            llm_analysis = {"raw": "LLM analysis failed."}

        all_results.append({
            "orig_name": orig_name,
            "saved_name": saved_name,
            "saved_path": saved_path,
            "kw_score": kw_score,
            "matched_kws": matched_kws,
            "missing_kws": missing_kws,
            "skills_found": skills_found,
            "yrs": yrs,
            "edu": edu,
            "format_checks": format_checks,
            "contact": contact,
            "readability": readability,
            "achievements": achievements,
            "generic_phrases": generic_phrases,
            "weak_verbs": weak_verbs,
            "rel_score": rel_score,
            "llm_analysis": llm_analysis
        })

    if len(all_results) == 0:
        flash("No valid resumes uploaded.")
        return redirect(url_for("home"))

    # Sort by relevance score desc
    all_results.sort(key=lambda x: x["rel_score"], reverse=True)

    # Determine how many to show/use: top_n between 1 and len(results)
    top_n = max(1, min(len(all_results), top_n))

    # Choose top_n (but we always show top 2 side-by-side for comparison if >=2)
    selected = all_results[:top_n]
    top2 = all_results[:2] if len(all_results) >= 2 else all_results[:1]

    # Similarity search on best resume (top 1)
    try:
        best_resume_text = ""
        with open(all_results[0]["saved_path"], "rb") as br:
            best_resume_text = extract_text_from_pdf(br)
        similarity = find_best_match(best_resume_text, top_k=5)
    except Exception:
        similarity = {"matches": []}

    return render_template("result_dashboard.html",
                           job_filename=job_filename_orig,
                           job_saved_name=job_saved_name,
                           top_n=top_n,
                           selected=selected,
                           top2=top2,
                           all_results=all_results,
                           similarity=similarity,
                           job_title=job_title,
                           linkedin_analysis=linkedin_analysis)


@app.route("/rewrite_bullet", methods=["POST"])
def rewrite_bullet_route():
    data = request.json or {}
    bullet = data.get("bullet", "")
    if not bullet:
        return jsonify({"error": "no bullet provided"}), 400
    try:
        new = rewrite_achievement(bullet)
        return jsonify({"rewritten": new})
    except Exception as e:
        LOG.exception("rewrite failed: %s", e)
        return jsonify({"error": "rewrite failed"}), 500


@app.route("/rewrite_full", methods=["POST"])
def rewrite_full_route():
    data = request.json or {}
    resume = data.get("resume", "")
    job = data.get("job", "")
    tone = data.get("tone", "leadership")
    if not resume or not job:
        return jsonify({"error": "resume and job required"}), 400
    try:
        new = full_resume_rewrite(resume, job, tone=tone)
        return jsonify({"rewritten_resume": new})
    except Exception as e:
        LOG.exception("full rewrite failed: %s", e)
        return jsonify({"error": "rewrite failed"}), 500


@app.route("/download/<path:filename>")
def download_file(filename):
    # Serve saved file (inline viewing)
    safe_path = safe_join(app.config["UPLOAD_FOLDER"], filename)
    if not safe_path:
        flash("Invalid file path.")
        return redirect(url_for("home"))
    if os.path.exists(safe_path):
        # Use send_file so browser can display if it supports PDFs inline
        return send_file(safe_path, as_attachment=False)
    flash("File not found.")
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True, port=8501)
