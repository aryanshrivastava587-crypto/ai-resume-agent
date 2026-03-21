# 🤖 AI Resume Agent

AI-powered Resume Analyzer & Career Recommender built with **Google Gemini LLM**, **RAG Pipeline** (FAISS + SentenceTransformers), **FastAPI**, and **Streamlit**.

---

## 🚀 Features

### 🏢 Recruiter Mode
Upload a candidate's resume and paste a job description — the AI analyzes the match using **context-based reasoning** (not keyword matching) and returns:
- **Match Score** (0–100)
- **Strong Points** identified from the resume
- **Missing Skills** based on job requirements
- **Actionable Suggestions** to improve the resume

### 🎓 Candidate Mode
Upload your resume — **no job description needed** — and the AI recommends:
- **Top 5 Job Roles** you should apply for (with confidence %)
- **Best Industries** for your profile
- **Current Strengths**
- **Skill Gaps** to work on
- **Personalized Career Advice**

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **LLM** | Google Gemini 2.5 Flash (Structured JSON Output) |
| **RAG Pipeline** | FAISS + SentenceTransformers (`all-MiniLM-L6-v2`) |
| **Backend** | FastAPI + Uvicorn |
| **Frontend** | Streamlit |
| **PDF Parsing** | pdfplumber |
| **Deployment** | Docker |

---

## 📁 Project Structure

```
ai-resume-agent/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI entry point with CORS
│   ├── routes.py               # /analyze & /recommend endpoints
│   └── services/
│       ├── llm_service.py      # Gemini LLM integration
│       ├── parser.py           # PDF text extraction
│       └── rag_service.py      # RAG pipeline (embeddings + FAISS)
├── data/
│   ├── jobs/job.txt            # Default job description
│   └── resumes/                # Uploaded resumes (gitignored)
├── frontend.py                 # Streamlit UI (dual-mode tabs)
├── test_parser.py              # Dev testing script
├── requirements.txt
├── Dockerfile
├── .gitignore
└── .dockerignore
```

---

## ⚡ Quick Start

### 1. Clone the repo
```bash
git clone https://github.com/aryanshrivastava587-crypto/ai-resume-agent.git
cd ai-resume-agent
```

### 2. Create virtual environment
```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Add your Gemini API key
Create a `.env` file in the root directory:
```
GEMINI_API_KEY=your_api_key_here
```
Get your free API key from [Google AI Studio](https://aistudio.google.com/apikey).

### 5. Run the application
Start the **backend** and **frontend** in two separate terminals:

```bash
# Terminal 1 — FastAPI Backend
uvicorn app.main:app

# Terminal 2 — Streamlit Frontend
streamlit run frontend.py
```

Open **http://localhost:8501** in your browser.

---

## 🐳 Docker

```bash
docker build -t ai-resume-agent .
docker run -e GEMINI_API_KEY=your_key -p 8000:8000 ai-resume-agent
```

---

## 🔑 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Health check |
| `POST` | `/analyze` | Recruiter Mode — upload resume + job description |
| `POST` | `/recommend` | Candidate Mode — upload resume only |

Interactive API docs available at **http://localhost:8000/docs**

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).
