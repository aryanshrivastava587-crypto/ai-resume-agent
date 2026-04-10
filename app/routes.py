import os
import logging
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request
from app.services.parser import extract_text_from_pdf
from app.services.llm_service import analyze_resume, recommend_roles
from app.rate_limiter import rate_limiter

logger = logging.getLogger(__name__)

UPLOAD_DIR = "data/resumes"

router = APIRouter(prefix="/api")


def _get_client_ip(request: Request) -> str:
    """Extract client IP, accounting for reverse proxies."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host


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


@router.get("/usage")
def usage(request: Request):
    """Get current rate limit status for the client."""
    ip = _get_client_ip(request)
    status = rate_limiter.get_status(ip)
    return status


@router.post("/analyze")
async def analyze(
    request: Request,
    file: UploadFile = File(...),
    job_description: str = Form(...)
):
    # ── Rate limit check ──
    ip = _get_client_ip(request)
    limit = rate_limiter.check(ip)
    if not limit["allowed"]:
        hours = limit["reset_in_seconds"] // 3600
        mins = (limit["reset_in_seconds"] % 3600) // 60
        raise HTTPException(
            status_code=429,
            detail=f"Daily limit reached ({limit['limit']} analyses/day). Resets in {hours}h {mins}m. Come back tomorrow!"
        )

    try:
        file_location = await _save_upload(file)
        resume = extract_text_from_pdf(file_location)

        if not job_description or not job_description.strip():
            raise HTTPException(status_code=400, detail="Job description is required.")

        result = analyze_resume(resume, job_description)
        result["_usage"] = {"remaining": limit["remaining"], "limit": limit["limit"]}
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in /api/analyze: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recommend")
async def recommend(
    request: Request,
    file: UploadFile = File(...)
):
    # ── Rate limit check ──
    ip = _get_client_ip(request)
    limit = rate_limiter.check(ip)
    if not limit["allowed"]:
        hours = limit["reset_in_seconds"] // 3600
        mins = (limit["reset_in_seconds"] % 3600) // 60
        raise HTTPException(
            status_code=429,
            detail=f"Daily limit reached ({limit['limit']} analyses/day). Resets in {hours}h {mins}m. Come back tomorrow!"
        )

    try:
        file_location = await _save_upload(file)
        resume = extract_text_from_pdf(file_location)
        result = recommend_roles(resume)
        result["_usage"] = {"remaining": limit["remaining"], "limit": limit["limit"]}
        return result

    except Exception as e:
        logger.error(f"Error in /api/recommend: {e}")
        raise HTTPException(status_code=500, detail=str(e))