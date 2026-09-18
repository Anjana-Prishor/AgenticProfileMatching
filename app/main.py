from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.services.matching import match_profiles, rank_candidates
from matching_agent import extract_requirements, tool_registry

try:
    from resume_rag import ResumeRAGSystem
except Exception:  # pragma: no cover
    ResumeRAGSystem = None


class CandidateProfile(BaseModel):
    name: str
    role: str
    experience_years: int = 0
    skills: list[str] = Field(default_factory=list)
    location: str | None = None
    preferences: dict[str, Any] = Field(default_factory=dict)


class MatchRequest(BaseModel):
    job_description: str
    candidates: list[CandidateProfile] = Field(default_factory=list)
    resume_directory: str | None = None


class ResumeDirectoryRequest(BaseModel):
    directory: str = Field(..., description="Directory containing resume files")


class ResumeSearchRequest(BaseModel):
    query: str = Field(..., description="Search text for resume retrieval")
    directory: str = Field(default="./sample_resumes")
    limit: int = Field(default=5)


app = FastAPI(title="Agentic Profile Matching API")


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/rag-search")
def rag_search_endpoint(request: ResumeSearchRequest) -> dict[str, Any]:
    if "rag_search" not in tool_registry or tool_registry["rag_search"] is None:
        raise HTTPException(status_code=500, detail="RAG search tool is not available")

    return tool_registry["rag_search"](request.query, request.directory, request.limit)


@app.post("/ingest-resumes")
def ingest_resumes(request: ResumeDirectoryRequest) -> dict[str, Any]:
    if ResumeRAGSystem is None:
        raise HTTPException(status_code=500, detail="Resume RAG system is not available")

    directory = Path(request.directory)
    if not directory.exists() or not directory.is_dir():
        raise HTTPException(status_code=400, detail=f"Directory not found: {request.directory}")

    rag = ResumeRAGSystem(db_path="./agent_chroma_db")
    results = rag.process_resumes_from_directory(str(directory))
    return {
        "directory": str(directory.resolve()),
        "processed": results.get("processed", 0),
        "failed": results.get("failed", 0),
        "resumes": results.get("resumes", []),
    }


@app.post("/match")
def match_candidates(request: MatchRequest) -> dict[str, Any]:
    reqs = extract_requirements(request.job_description)

    candidate_profiles = [candidate.model_dump() for candidate in request.candidates]
    if not candidate_profiles and request.resume_directory:
        if ResumeRAGSystem is None:
            raise HTTPException(status_code=500, detail="Resume RAG system is not available")

        rag = ResumeRAGSystem(db_path="./agent_chroma_db")
        results = rag.process_resumes_from_directory(request.resume_directory)
        candidate_profiles = [
            {
                "name": resume.get("name", "Unknown"),
                "role": "Backend Engineer",
                "experience_years": int(resume.get("experience_years", 0)),
                "skills": resume.get("skills", []),
                "location": None,
                "preferences": {"remote": True},
            }
            for resume in results.get("resumes", [])
        ]

    target = {
        "name": "Target",
        "role": "Backend Engineer",
        "experience_years": 0,
        "skills": [
            skill for item in reqs.get("must_have", []) for skill in item.split() if len(item.split()) <= 3
        ],
        "location": None,
        "preferences": {"remote": True},
    }

    ranked = rank_candidates(target, candidate_profiles)

    matches = []
    for candidate in ranked:
        score = match_profiles(target, candidate)
        matches.append({
            "name": candidate["name"],
            "role": candidate["role"],
            "score": score,
            "match_score": candidate.get("match_score", score),
        })

    report_lines = [
        "Candidate Recommendation Report",
        "------------------------------",
        f"Job requirements: {reqs}",
    ]
    for item in matches:
        report_lines.append(f"- {item['name']} ({item['role']}): {item['score']}")

    return {
        "report": "\n".join(report_lines),
        "matches": matches,
        "requirements": reqs,
    }
