import logging
import json
import time

import google.generativeai as genai
from app.services.rag_service import create_embeddings, build_index, retrieve

logger = logging.getLogger(__name__)

_JSON_CONFIG = genai.GenerationConfig(response_mime_type="application/json")


def _call_gemini(prompt: str, api_key: str, max_retries: int = 3):
    """Call Gemini with structured JSON output and the user's API key."""
    genai.configure(api_key=api_key)
    for attempt in range(max_retries):
        try:
            _gemini_model = genai.GenerativeModel("gemini-flash-latest")
            response = _gemini_model.generate_content(
                prompt, 
                generation_config=_JSON_CONFIG,
                request_options={"retry": None, "timeout": 20}
            )
            return json.loads(response.text)
        except Exception as e:
            err_str = str(e).lower()
            if "429" in err_str or "quota" in err_str:
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 3
                    logger.warning(f"Rate limit hit! Waiting {wait_time}s to retry... (attempt {attempt+2}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error("All retries exhausted.")
                    raise Exception(f"Google API limits exhausted for your key. Details: {str(e)}")
            else:
                raise Exception(f"Google API Error: {str(e)}")


# ── Recruiter Mode ────────────────────────────────────────────
def analyze_resume(resume: str, job: str, api_key: str):
    """Analyze a resume against a specific job description."""
    logger.info("Recruiter Mode: Starting resume analysis (direct fast-path)")
    start = time.time()

    # Pass the full resume directly to Gemini (no RAG needed since context is 1M tokens)
    resume_context = resume.strip() if resume else "No readable text found."

    logger.info(f"Context prepared in {time.time() - start:.3f}s")

    prompt = f"""
    You are an expert recruiter and resume analyzer capable of handling ANY industry, domain, or job title.
    Perform context-based reasoning to truly understand the candidate's experience and how it maps to the job.
    
    Job Description:
    {job}
    
    Resume Snippets (from candidate):
    {resume_context}
    
    Analyze the match. Do not rely on simple keyword matching. 
    1. Determine a contextual match_score (0-100).
    2. Extract strong_points based on inferred skills.
    3. Identify missing_skills by truly understanding the job requirements.
    4. Provide actionable suggestions to improve the resume.
    """

    try:
        result = _call_gemini(prompt, api_key)
        result.setdefault("match_score", 0)
        result.setdefault("strong_points", [])
        result.setdefault("missing_skills", [])
        result.setdefault("suggestions", [])
        logger.info(f"Analysis complete. Match score: {result['match_score']}")
        return result

    except Exception as e:
        logger.error(f"Gemini API error during analysis: {e}")
        return {
            "match_score": 0,
            "strong_points": [],
            "missing_skills": [],
            "suggestions": [f"Error occurred during analysis: {str(e)}"]
        }


# ── Candidate Mode ────────────────────────────────────────────
def recommend_roles(resume: str, api_key: str):
    """Analyze a resume and recommend best-fit job roles."""
    logger.info("Candidate Mode: Starting role recommendation (direct fast-path)")
    start = time.time()

    # Pass the full resume directly to Gemini (no RAG needed since context is 1M tokens)
    resume_context = resume.strip() if resume else "No readable text found."

    logger.info(f"Context prepared in {time.time() - start:.3f}s")

    prompt = f"""
    You are a world-class career advisor and talent strategist with deep knowledge across ALL industries — tech, finance, healthcare, marketing, design, operations, and more.

    A student/job-seeker has shared their resume below. They do NOT know what job roles suit them best.

    Resume:
    {resume_context}

    Based on a deep contextual understanding of their skills, projects, education, and experience, provide:

    1. "recommended_roles": A list of 5 specific job titles they should apply for (e.g., "Junior Data Analyst", "Backend Developer Intern", "ML Engineer"). Be specific, not generic.
    2. "confidence": For each role, a confidence percentage (0-100) of how well their resume fits that role RIGHT NOW.
    3. "industry_fit": Top 3 industries where this candidate would thrive (e.g., "FinTech", "EdTech", "Healthcare AI").
    4. "current_strengths": What this candidate is already strong at.
    5. "skill_gaps": What skills they should learn ASAP to become more employable.
    6. "career_advice": 3-4 lines of honest, actionable career advice for this person.

    Return the result as a JSON object with this exact structure:
    {{
        "recommended_roles": [
            {{"title": "Role Name", "confidence": 85, "reason": "Why this role fits"}},
            ...
        ],
        "industry_fit": ["Industry1", "Industry2", "Industry3"],
        "current_strengths": ["Strength1", "Strength2"],
        "skill_gaps": ["Skill1", "Skill2"],
        "career_advice": "Your honest advice here."
    }}
    """

    try:
        result = _call_gemini(prompt, api_key)
        result.setdefault("recommended_roles", [])
        result.setdefault("industry_fit", [])
        result.setdefault("current_strengths", [])
        result.setdefault("skill_gaps", [])
        result.setdefault("career_advice", "No advice generated.")
        logger.info(f"Recommendation complete. {len(result['recommended_roles'])} roles suggested.")
        return result

    except Exception as e:
        logger.error(f"Gemini API error during recommendation: {e}")
        return {
            "recommended_roles": [],
            "industry_fit": [],
            "current_strengths": [],
            "skill_gaps": [],
            "career_advice": f"Error occurred: {str(e)}"
        }