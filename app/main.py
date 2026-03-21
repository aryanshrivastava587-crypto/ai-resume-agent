import os
import logging
from dotenv import load_dotenv

load_dotenv()

# Configure logging for the entire application
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import router

app = FastAPI(
    title="AI Resume Agent",
    description="AI-powered resume analysis and career recommendation tool using Google Gemini LLM and RAG.",
    version="1.0.0",
)

# CORS — allow the Streamlit frontend (and any other client) to access the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)