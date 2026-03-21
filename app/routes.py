import os
import logging
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.services.parser import extract_text_from_pdf
from app.services.llm_service import analyze_resume, recommend_roles

logger = logging.getLogger(__name__)

UPLOAD_DIR = "data/resumes"

router = APIRouter()


async def _save_upload(file: UploadFile) -> str:
    """Helper to save an uploaded file and return the path."""
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_location = os.path.join(UPLOAD_DIR, file.filename)
    contents = await file.read()
    with open(file_location, "wb") as f:
        f.write(contents)
    logger.info(f"Saved uploaded file: {file_location} ({len(contents)} bytes)")
    return file_location


@router.get("/")
def home():
    return {"message": "AI Resume Agent Running", "version": "1.0.0"}


@router.post("/analyze")
async def analyze(
    file: UploadFile = File(...),
    job_description: str = Form(None)
):
    try:
        file_location = await _save_upload(file)
        resume = extract_text_from_pdf(file_location)

        if job_description:
            job = job_description
        else:
            job_file = "data/jobs/job.txt"
            if not os.path.exists(job_file):
                raise HTTPException(status_code=400, detail="No job description provided and default job.txt not found.")
            with open(job_file, "r", encoding="utf-8") as f:
                job = f.read()

        result = analyze_resume(resume, job)
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in /analyze: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recommend")
async def recommend(file: UploadFile = File(...)):
    try:
        file_location = await _save_upload(file)
        resume = extract_text_from_pdf(file_location)
        result = recommend_roles(resume)
        return result

    except Exception as e:
        logger.error(f"Error in /recommend: {e}")
        raise HTTPException(status_code=500, detail=str(e))