import streamlit as st
import requests

st.set_page_config(page_title="AI Resume Agent", page_icon="🤖", layout="centered")

# Custom CSS for a polished look
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1rem 0;
    }
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

st.title("🤖 AI Resume Agent")
st.caption("Powered by Google Gemini LLM | RAG Pipeline | FastAPI")

# Two-mode tabs
tab1, tab2 = st.tabs(["🏢 Recruiter Mode", "🎓 Candidate Mode"])

# ─────────────────────────────────────────────
# TAB 1: RECRUITER MODE
# ─────────────────────────────────────────────
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
                    files = {"file": (recruiter_file.name, recruiter_file.getvalue(), "application/pdf")}
                    data = {"job_description": job_desc}

                    response = requests.post("http://127.0.0.1:8000/analyze", files=files, data=data)

                    if response.status_code == 200:
                        result = response.json()

                        st.success("✅ Analysis Complete!")

                        # Score Display
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

                    else:
                        st.error(f"API Error: {response.text}")
                except Exception as e:
                    st.error(f"Connection failed. Is the FastAPI server running? Error: {e}")
        else:
            st.warning("⚠️ Please upload a resume AND paste a job description.")


# ─────────────────────────────────────────────
# TAB 2: CANDIDATE MODE
# ─────────────────────────────────────────────
with tab2:
    st.header("🎓 Candidate Mode")
    st.markdown("Upload your resume and discover which job roles are the **best fit for you** — no job description needed!")

    st.subheader("Upload Your Resume")
    candidate_file = st.file_uploader("Upload PDF Resume", type=["pdf"], key="candidate_file")

    if st.button("🚀 Find My Best Roles", type="primary", key="candidate_btn"):
        if candidate_file is not None:
            with st.spinner("Gemini AI is analyzing your profile and finding the best roles for you..."):
                try:
                    files = {"file": (candidate_file.name, candidate_file.getvalue(), "application/pdf")}

                    response = requests.post("http://127.0.0.1:8000/recommend", files=files)

                    if response.status_code == 200:
                        result = response.json()

                        st.success("✅ Role Recommendations Ready!")
                        st.divider()

                        # Recommended Roles
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

                        # Industry Fit
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

                        # Skill Gaps
                        st.subheader("📚 Skills You Should Learn Next")
                        for skill in result.get("skill_gaps", []):
                            st.warning(f"📌 {skill}")

                        st.divider()

                        # Career Advice
                        st.subheader("🧭 Career Advice")
                        st.info(result.get("career_advice", "No advice available."))

                    else:
                        st.error(f"API Error: {response.text}")
                except Exception as e:
                    st.error(f"Connection failed. Is the FastAPI server running? Error: {e}")
        else:
            st.warning("⚠️ Please upload your resume first.")
