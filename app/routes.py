import os
import logging
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request
from app.services.parser import extract_text_from_pdf
from app.services.llm_service import analyze_resume, recommend_roles

logger = logging.getLogger(__name__)

UPLOAD_DIR = "data/resumes"

router = APIRouter(prefix="/api")


async def _save_upload(file: UploadFile) -> str:
    """Helper to save an uploaded file and return the path."""
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_location = os.path.join(UPLOAD_DIR, file.filename)
    contents = await file.read()
    with open(file_location, "wb") as f:
        f.write(contents)
    logger.info(f"Saved uploaded file: {file_location} ({len(contents)} bytes)")
    return file_location


@router.get("/health")
def health():
    return {"message": "AI Resume Agent Running", "version": "2.0.0"}


@router.post("/analyze")
async def analyze(
    request: Request,
    file: UploadFile = File(...),
    job_description: str = Form(...),
    api_key: str = Form(...)
):
    try:
        file_location = await _save_upload(file)
        resume = extract_text_from_pdf(file_location)

        if not job_description or not job_description.strip():
            raise HTTPException(status_code=400, detail="Job description is required.")

        if not api_key or not api_key.strip():
            raise HTTPException(status_code=400, detail="API key is required.")

        result = analyze_resume(resume, job_description, api_key.strip())
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in /api/analyze: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recommend")
async def recommend(
    request: Request,
    file: UploadFile = File(...),
    api_key: str = Form(...)
):
    try:
        file_location = await _save_upload(file)
        resume = extract_text_from_pdf(file_location)

        if not api_key or not api_key.strip():
            raise HTTPException(status_code=400, detail="API key is required.")

        result = recommend_roles(resume, api_key.strip())
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in /api/recommend: {e}")
        raise HTTPException(status_code=500, detail=str(e))