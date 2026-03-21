import streamlit as st
import os
import json
import tempfile

# ── Page Config ──
st.set_page_config(page_title="AI Resume Agent", page_icon="🤖", layout="centered")

# ── Load API Key (Streamlit Cloud uses st.secrets, local uses .env) ──
api_key = None
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except Exception:
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    st.error("⚠️ GEMINI_API_KEY not found. Please set it in Streamlit Secrets or a .env file.")
    st.stop()

# ── Import services (lazy load heavy libraries) ──
@st.cache_resource
def load_services():
    """Load heavy ML models once and cache them across sessions."""
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")
    
    from sentence_transformers import SentenceTransformer
    embed_model = SentenceTransformer('all-MiniLM-L6-v2')
    
    return genai, model, embed_model

genai_lib, gemini_model, embed_model = load_services()

# ── Helper Functions ──
import numpy as np
import faiss
import pdfplumber


def extract_text_from_pdf(file_bytes):
    """Extract text from uploaded PDF bytes."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    text_parts = []
    try:
        with pdfplumber.open(tmp_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
    finally:
        os.unlink(tmp_path)

    return "\n\n".join(text_parts) if text_parts else "No readable text found."


def split_and_embed(text):
    """Split text into chunks and create embeddings."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if len(paragraphs) < 3:
        paragraphs = [line.strip() for line in text.split("\n") if line.strip()]
    
    # Merge short fragments
    merged = []
    buffer = ""
    for p in paragraphs:
        if len(buffer) + len(p) < 300:
            buffer = f"{buffer} {p}".strip()
        else:
            if buffer:
                merged.append(buffer)
            buffer = p
    if buffer:
        merged.append(buffer)
    
    chunks = merged[:20] if merged else ["No content available."]
    embeddings = embed_model.encode(chunks, show_progress_bar=False)
    return chunks, np.array(embeddings)


def retrieve_relevant(query, chunks, embeddings, k=5):
    """Retrieve top-k relevant chunks using FAISS."""
    k = min(k, len(chunks))
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)
    query_emb = embed_model.encode([query])
    D, I = index.search(np.array(query_emb), k)
    return [chunks[i] for i in I[0] if i < len(chunks)]


def call_gemini(prompt):
    """Call Gemini with structured JSON output."""
    config = genai_lib.GenerationConfig(response_mime_type="application/json")
    response = gemini_model.generate_content(prompt, generation_config=config)
    return json.loads(response.text)


# ── Custom CSS ──
st.markdown("""
<style>
    .role-card {
        background: linear-gradient(135deg, #1a1a2e, #16213e);
        border: 1px solid #0f3460;
        border-radius: 12px;
        padding: 1.2rem;
        margin-bottom: 0.8rem;
    }
    .confidence-high { color: #00e676; font-weight: bold; }
    .confidence-mid { color: #ffab00; font-weight: bold; }
    .confidence-low { color: #ff5252; font-weight: bold; }
</style>
""", unsafe_allow_html=True)


# ── Main UI ──
st.title("🤖 AI Resume Agent")
st.caption("Powered by Google Gemini LLM | RAG Pipeline | FastAPI")

tab1, tab2 = st.tabs(["🏢 Recruiter Mode", "🎓 Candidate Mode"])


# ─── TAB 1: RECRUITER MODE ─────────────────────
with tab1:
    st.header("🏢 Recruiter Mode")
    st.markdown("Upload a candidate's resume and paste the job description to get an AI-powered match analysis.")

    st.subheader("1. Candidate Resume")
    recruiter_file = st.file_uploader("Upload PDF Resume", type=["pdf"], key="recruiter_file")

    st.subheader("2. Job Description")
    job_desc = st.text_area("Paste the job description here...", height=200, key="recruiter_jd")

    if st.button("🔍 Analyze Match", type="primary", key="recruiter_btn"):
        if recruiter_file is not None and job_desc:
            with st.spinner("Gemini AI is analyzing the match..."):
                try:
                    resume_text = extract_text_from_pdf(recruiter_file.getvalue())
                    chunks, embeddings = split_and_embed(resume_text)
                    relevant = retrieve_relevant(job_desc, chunks, embeddings)
                    resume_context = "\n\n".join(relevant)

                    prompt = f"""
                    You are an expert recruiter and resume analyzer capable of handling ANY industry, domain, or job title.
                    Perform context-based reasoning to truly understand the candidate's experience and how it maps to the job.
                    
                    Job Description:
                    {job_desc}
                    
                    Resume Snippets (from candidate):
                    {resume_context}
                    
                    Analyze the match. Do not rely on simple keyword matching.
                    1. Determine a contextual match_score (0-100).
                    2. Extract strong_points based on inferred skills.
                    3. Identify missing_skills by truly understanding the job requirements.
                    4. Provide actionable suggestions to improve the resume.
                    """

                    result = call_gemini(prompt)

                    st.success("✅ Analysis Complete!")

                    score = result.get("match_score", 0)
                    if score >= 80:
                        st.metric("Match Score", f"{score}/100", "🟢 Excellent Fit", delta_color="normal")
                    elif score >= 50:
                        st.metric("Match Score", f"{score}/100", "🟡 Moderate Fit", delta_color="off")
                    else:
                        st.metric("Match Score", f"{score}/100", "🔴 Low Fit", delta_color="inverse")

                    st.divider()

                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader("✅ Strong Points")
                        for point in result.get("strong_points", []):
                            st.write(f"• {point}")
                    with col2:
                        st.subheader("❌ Missing Skills")
                        for skill in result.get("missing_skills", []):
                            st.write(f"• {skill}")

                    st.divider()
                    st.subheader("💡 Suggestions")
                    for suggestion in result.get("suggestions", []):
                        st.info(suggestion)

                except Exception as e:
                    st.error(f"Error: {e}")
        else:
            st.warning("⚠️ Please upload a resume AND paste a job description.")


# ─── TAB 2: CANDIDATE MODE ─────────────────────
with tab2:
    st.header("🎓 Candidate Mode")
    st.markdown("Upload your resume and discover which job roles are the **best fit for you** — no job description needed!")

    st.subheader("Upload Your Resume")
    candidate_file = st.file_uploader("Upload PDF Resume", type=["pdf"], key="candidate_file")

    if st.button("🚀 Find My Best Roles", type="primary", key="candidate_btn"):
        if candidate_file is not None:
            with st.spinner("Gemini AI is analyzing your profile and finding the best roles for you..."):
                try:
                    resume_text = extract_text_from_pdf(candidate_file.getvalue())
                    chunks, embeddings = split_and_embed(resume_text)
                    resume_context = "\n\n".join(chunks)

                    prompt = f"""
                    You are a world-class career advisor and talent strategist with deep knowledge across ALL industries.

                    A student/job-seeker has shared their resume below. They do NOT know what job roles suit them best.

                    Resume:
                    {resume_context}

                    Based on a deep contextual understanding of their skills, projects, education, and experience, provide:
                    1. "recommended_roles": A list of 5 specific job titles with confidence (0-100) and reason.
                    2. "industry_fit": Top 3 industries where this candidate would thrive.
                    3. "current_strengths": What this candidate is already strong at.
                    4. "skill_gaps": What skills they should learn ASAP.
                    5. "career_advice": 3-4 lines of honest, actionable career advice.

                    Return as JSON:
                    {{
                        "recommended_roles": [{{"title": "Role", "confidence": 85, "reason": "Why"}}],
                        "industry_fit": ["Industry1", "Industry2", "Industry3"],
                        "current_strengths": ["Strength1", "Strength2"],
                        "skill_gaps": ["Skill1", "Skill2"],
                        "career_advice": "Your advice here."
                    }}
                    """

                    result = call_gemini(prompt)

                    st.success("✅ Role Recommendations Ready!")
                    st.divider()

                    st.subheader("🎯 Recommended Job Roles for You")
                    for role in result.get("recommended_roles", []):
                        title = role.get("title", "Unknown")
                        confidence = role.get("confidence", 0)
                        reason = role.get("reason", "")

                        if confidence >= 75:
                            color_class = "confidence-high"
                            emoji = "🟢"
                        elif confidence >= 50:
                            color_class = "confidence-mid"
                            emoji = "🟡"
                        else:
                            color_class = "confidence-low"
                            emoji = "🔴"

                        st.markdown(f"""
                        <div class="role-card">
                            <h4>{emoji} {title} — <span class="{color_class}">{confidence}% Match</span></h4>
                            <p style="color: #aaa; margin: 0;">{reason}</p>
                        </div>
                        """, unsafe_allow_html=True)

                    st.divider()

                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader("🏭 Best Industries for You")
                        for industry in result.get("industry_fit", []):
                            st.write(f"• {industry}")
                    with col2:
                        st.subheader("💪 Your Strengths")
                        for strength in result.get("current_strengths", []):
                            st.write(f"• {strength}")

                    st.divider()

                    st.subheader("📚 Skills You Should Learn Next")
                    for skill in result.get("skill_gaps", []):
                        st.warning(f"📌 {skill}")

                    st.divider()

                    st.subheader("🧭 Career Advice")
                    st.info(result.get("career_advice", "No advice available."))

                except Exception as e:
                    st.error(f"Error: {e}")
        else:
            st.warning("⚠️ Please upload your resume first.")
