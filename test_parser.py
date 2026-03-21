import os
from dotenv import load_dotenv
load_dotenv()

from app.services.parser import extract_text_from_pdf
from app.services.llm_service import analyze_resume

resume = extract_text_from_pdf("data/resumes/sample.pdf")

with open("data/jobs/job.txt", "r", encoding="utf-8") as f:
    job = f.read()

result = analyze_resume(resume, job)

print(result)