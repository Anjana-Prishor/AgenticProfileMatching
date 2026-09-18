from __future__ import annotations

from pathlib import Path

from app.services.matching import rank_candidates
from matching_agent import extract_requirements, rag_search, tool_registry


# Build a target profile based on the job description.
# This function extracts skills and other requirements from the job description.
def build_target_profile(job_description: str) -> dict:
    requirements = extract_requirements(job_description)
    skills = []
    for item in requirements.get("must_have", []):
        for token in item.split():
            token = token.strip(" ,;:-")
            if token and len(token) > 2:
                skills.append(token)

    return {
        "name": "Target",
        "role": "Backend Engineer",
        "experience_years": 5,
        "skills": list(dict.fromkeys(skills))[:10],
        "location": "Bengaluru",
        "preferences": {"remote": True, "industry": "fintech"},
    }


def build_candidates_from_rag(job_description: str, resume_directory: str) -> list[dict]:
    query = job_description
    results = rag_search(query=query, directory=resume_directory, limit=5)

    candidates = []
    for result in results.get("results", []):
        candidate = {
            "name": result.get("candidate_name", "Unknown Candidate"),
            "role": "Backend Engineer",
            "experience_years": int(result.get("experience_years", 0) or 0),
            "skills": result.get("skills", []),
            "location": "Remote",
            "preferences": {"remote": True, "industry": "fintech"},
        }
        candidates.append(candidate)

    if not candidates:
        candidates = [
            {
                "name": "Aarav",
                "role": "Backend Engineer",
                "experience_years": 5,
                "skills": ["Python", "FastAPI", "PostgreSQL", "Redis"],
                "location": "Bengaluru",
                "preferences": {"remote": True, "industry": "fintech"},
            },
            {
                "name": "Meera",
                "role": "Backend Engineer",
                "experience_years": 4,
                "skills": ["Python", "Django", "Redis", "SQL"],
                "location": "Pune",
                "preferences": {"remote": True, "industry": "fintech"},
            },
        ]

    return candidates


def load_job_description(filepath: str) -> str:
    result = tool_registry["read_file"](filepath)
    if not result.get("success"):
        raise RuntimeError(f"Unable to load job description: {result.get('error', 'unknown error')}")
    return result["content"]


def main() -> None:
    project_root = Path(__file__).resolve().parent
    job_description_path = project_root / "job_descriptions" / "current_job_description.txt"
    job_description = load_job_description(str(job_description_path))

    resume_directory = str(project_root / "milestone2_rag_profile_matching" / "sample_resumes")

    target = build_target_profile(job_description)
    candidates = build_candidates_from_rag(job_description, resume_directory)
    ranked = rank_candidates(target, candidates)

    print("Job requirements:")
    print(extract_requirements(job_description))
    print("\nTop candidates:")
    for idx, candidate in enumerate(ranked[:5], start=1):
        print(f"{idx}. {candidate['name']} -> match score: {candidate.get('match_score', 0)}")
        print(f"   Skills: {candidate.get('skills', [])}")
        print(f"   Experience: {candidate.get('experience_years', 0)} years")


if __name__ == "__main__":
    main()
