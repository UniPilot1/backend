"""
UniPilot — FastAPI Backend
Entry point. Run with: uvicorn main:app --reload
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from routers.api import matching_router, profile_router, gap_router, ai_router

app = FastAPI(
    title="UniPilot API",
    description="AI-powered university admissions strategy platform backend.",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://unipilot.vercel.app",
        os.getenv("FRONTEND_URL", "http://localhost:3000"),
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(matching_router, prefix="/api/v1")
app.include_router(profile_router,  prefix="/api/v1")
app.include_router(gap_router,      prefix="/api/v1")
app.include_router(ai_router,       prefix="/api/v1")

@app.get("/health")
def health():
    return {"status": "ok", "service": "UniPilot API", "version": "2.0.0"}

@app.get("/")
def root():
    return {
        "message": "UniPilot API v2",
        "docs": "/docs",
        "endpoints": {
            "match":   "/api/v1/match/",
            "profile": "/api/v1/profile/evaluate",
            "gap":     "/api/v1/gap/",
            "ai":      "/api/v1/ai/insight",
            "roadmap": "/api/v1/ai/roadmap",
        },
    }
