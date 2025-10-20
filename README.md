
# 📄 AI Resume Analyzer — Flask Edition

An advanced **AI-powered Resume Analyzer** built using **Flask**, **OpenAI**, and **Pinecone**, designed to compare resumes with job descriptions, evaluate ATS metrics, and generate intelligent AI insights — now with LinkedIn integration and multi-resume ranking.

---

## 🚀 Features

### 🔍 Core ATS Analysis
The analyzer evaluates resumes across these professional dimensions:

```bash
1. Keywords
2. Experience
3. Education
4. Skills
5. Format / Structure
6. Contact Information
7. Language & Readability
8. Achievements / Metrics
9. Relevance Score
```

### 🤖 AI & LinkedIn Integration
```bash
✔ GPT-4 based AI suggestions and resume comparison
✔ LinkedIn profile analysis (via public data)
✔ Strengths, Missing Skills, and Fit Score generation
✔ Tone detection and role suggestions
```

### 📊 Multi-Resume Comparison
```bash
✔ Upload multiple resumes (PDF)
✔ Compare them against one job description
✔ Auto-rank top 1–20 candidates by Relevance Score
✔ Interactive dashboard with ATS breakdown and gauge charts
```

### 💼 Resume Preview
```bash
✔ Embedded PDF viewer for each resume
✔ ATS metrics, AI analysis, and LinkedIn data displayed side by side
```

---

## 🧱 Project Structure

```bash
resume-analyzer/
├── app.py
├── requirements.txt
├── .env
│
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── resume_parser.py
│   ├── embeddings.py
│   ├── matcher.py
│   ├── ats_analyzer.py
│   ├── llm_analyzer.py
│   └── utils.py
│
├── templates/
│   ├── index.html
│   └── result_dashboard.html
│
└── static/
    ├── css/styles.css
    └── js/main.js
```

---

## ⚙️ Installation Guide

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/yourusername/resume-analyzer.git
cd resume-analyzer
```

### 2️⃣ Create a Virtual Environment
```bash
# For Windows
python -m venv venv
venv\Scripts\activate

# For macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```

### 4️⃣ Set Environment Variables
Create a `.env` file in the project root and add:
```bash
OPENAI_API_KEY=sk-xxxxxx
PINECONE_API_KEY=xxxxxx
PINECONE_INDEX_NAME=resumes-index
PINECONE_ENV=us-east1-gcp
```

---

## ▶️ Run the Flask App

```bash
python app.py
```

Once started, open your browser and visit:
```bash
http://127.0.0.1:5000/
```

---

## 🧩 How It Works

```bash
STEP 1: Upload one or more resumes (PDF)
STEP 2: Upload a job description (PDF)
STEP 3: Optionally enter a LinkedIn profile URL
STEP 4: Click "Analyze" to generate ATS + AI insights
STEP 5: View results in the interactive dashboard
```

---

## 🧠 Tech Stack

| Component | Technology |
|------------|-------------|
| **Backend** | Flask |
| **Frontend** | Tailwind CSS, Chart.js |
| **AI Model** | OpenAI GPT-4o-mini |
| **Vector DB** | Pinecone |
| **Parsing** | pdfplumber |
| **Environment** | python-dotenv |

---

## 🧮 Tips & Notes

```bash
⚠️ Keep your .env file private — never share your API keys.
⚙️ Ensure Pinecone index dimension = 1536 (for text-embedding-3-small).
📄 Use PDFs under 2MB for optimal analysis.
🚀 Compatible with OpenAI SDK v1.0.0+ and Pinecone SDK v3+.
```

---

## 🧠 Future Enhancements

```bash
✔ Resume improvement suggestions (AI rewrite)
✔ Compare one resume across multiple job roles
✔ Export detailed analysis reports (PDF)
✔ Integration with live job feeds (LinkedIn / Indeed API)
```

---

## 📧 Contact & Support

```bash
Author: Your Name
Email: yourname@example.com
LinkedIn: https://linkedin.com/in/yourprofile
```

---

## ⭐ Contribute

```bash
# Fork the repo
# Create a new feature branch
git checkout -b feature/amazing-feature

# Commit your changes
git commit -m "Add amazing feature"

# Push to the branch
git push origin feature/amazing-feature
```

Then open a **Pull Request** 🎉

---

## 🛡 License
This project is released under the **MIT License** — free for personal and commercial use.

---

> Made with ❤️ using Flask, OpenAI, Pinecone & TailwindCSS
````

---

