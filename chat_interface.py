from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.services.matching import match_profiles, rank_candidates
from matching_agent import (
    compare_candidates,
    explain_candidate_match,
    generate_interview_questions,
    parse_natural_language_query,
    tool_registry,
)


@dataclass
class ConversationSession:
    """Small CLI conversation state that preserves requirements and shortlist."""

    job_description: str
    candidates: list[dict[str, Any]]
    history: list[dict[str, str]] = field(default_factory=list)
    active_filters: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.active_filters = parse_natural_language_query(self.job_description)
        self._rerank()

    def _target_profile(self) -> dict[str, Any]:
        filters = self.active_filters
        return {
            "name": "Target",
            "role": "Backend Engineer",
            "experience_years": filters.get("min_experience", 0),
            "skills": filters.get("skills", []),
            "location": None,
            "preferences": {},
        }

    def _rerank(self) -> None:
        filters = self.active_filters
        eligible = [
            candidate
            for candidate in self.candidates
            if candidate.get("experience_years", 0) >= filters.get("min_experience", 0)
            and all(
                skill in {item.lower() for item in candidate.get("skills", [])}
                for skill in filters.get("skills", [])
            )
        ]
        target = self._target_profile()
        scored_candidates = []
        for candidate in eligible:
            # A minimum-years filter is a floor, not an exact target. Avoid
            # penalizing candidates who have more experience than requested.
            scoring_target = {**target, "experience_years": candidate.get("experience_years", 0)}
            scored_candidates.append({
                **candidate,
                "match_score": match_profiles(scoring_target, candidate),
                "experience_fit": "exceeds minimum" if candidate.get("experience_years", 0) > filters.get("min_experience", 0) else "meets minimum",
            })
        self.shortlist = sorted(
            scored_candidates,
            key=lambda item: (item["match_score"], item.get("experience_years", 0)),
            reverse=True,
        )

    def ask(self, query: str) -> str:
        """Handle one natural-language request and return a human-readable answer."""
        self.history.append({"role": "user", "content": query})
        normalized = query.lower().strip()

        if any(command in normalized for command in ("find", "show", "search")) or "years" in normalized:
            new_filters = parse_natural_language_query(query)
            requested_filters = {
                key: value for key, value in new_filters.items()
                if value not in ([], 0, False)
            }
            if new_filters["skills"]:
                self.active_filters["skills"] = new_filters["skills"]
            if new_filters["min_experience"]:
                self.active_filters["min_experience"] = new_filters["min_experience"]
            self.active_filters.update(requested_filters)
            self._rerank()
            answer = self._format_shortlist("Updated shortlist")
        elif "compare" in normalized or "side by side" in normalized:
            selected = self.shortlist[:3]
            comparison = compare_candidates([item["name"] for item in selected])
            answer = "Side-by-side comparison:\n" + "\n".join(
                f"- {item['candidate_id']}: {item['summary']}"
                for item in comparison
            )
        elif "why" in normalized or "rank" in normalized:
            names = re.findall(r"[A-Z][a-z]+", query)
            selected = [item for item in self.shortlist if item["name"] in names]
            if len(selected) < 2:
                selected = self.shortlist[:2]
            target = self._target_profile()
            answer = "Ranking explanation:\n" + "\n".join(
                f"- {item['name']}: score={item.get('match_score', 0)}, "
                f"experience={item.get('experience_years', 0)} years "
                f"({item.get('experience_fit', 'not evaluated')}); "
                f"details={explain_candidate_match(item, target)}"
                for item in selected
            )
        elif "interview" in normalized or "screening questions" in normalized:
            candidate = self.shortlist[0] if self.shortlist else {"name": "candidate"}
            questions = generate_interview_questions(candidate["name"])
            answer = "Interview questions:\n" + "\n".join(f"- {question}" for question in questions)
        else:
            answer = self._format_shortlist("Current shortlist")

        self.history.append({"role": "agent", "content": answer})
        return answer

    def _format_shortlist(self, heading: str) -> str:
        if not self.shortlist:
            return f"{heading}: no candidates match the active requirements."
        lines = [f"{heading}:"]
        for index, candidate in enumerate(self.shortlist[:10], start=1):
            lines.append(
                f"{index}. {candidate['name']} | {candidate.get('role', 'Unknown')} | "
                f"score={candidate.get('match_score', 0)} | "
                f"experience={candidate.get('experience_years', 0)} years"
            )
        return "\n".join(lines)


def default_candidates() -> list[dict[str, Any]]:
    """Return deterministic candidates for unit tests and lightweight examples."""
    return [
        {"name": "Aarav", "role": "Backend Engineer", "experience_years": 5, "skills": ["Python", "FastAPI", "PostgreSQL", "Redis"]},
        {"name": "Nisha", "role": "Backend Engineer", "experience_years": 4, "skills": ["Python", "FastAPI", "SQL", "Redis"]},
        {"name": "Rohan", "role": "Frontend Engineer", "experience_years": 3, "skills": ["React", "JavaScript"]},
    ]


def load_sample_candidates(directory: str | Path | None = None) -> list[dict[str, Any]]:
    """Load candidate profiles from the repository's real resume corpus."""
    resume_directory = Path(directory) if directory else Path(__file__).resolve().parent / "milestone2_rag_profile_matching" / "sample_resumes"
    files = tool_registry["list_files"](str(resume_directory), ".txt")
    candidates = []
    known_skills = [
        "python", "fastapi", "django", "flask", "sql", "postgresql", "mysql", "redis",
        "react", "javascript", "typescript", "node.js", "java", "go", "docker", "kubernetes",
        "aws", "azure", "gcp", "spark", "airflow", "tensorflow", "pytorch", "graphql",
    ]

    for file_info in files:
        if not file_info.get("path"):
            continue
        result = tool_registry["read_file"](file_info["path"])
        if not result.get("success"):
            continue
        content = result.get("content", "")
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        name = lines[0] if lines else Path(file_info["path"]).stem.replace("_", " ").title()
        lowered = content.lower()
        skills = [skill.title() for skill in known_skills if skill in lowered]
        years_match = re.search(r"(\d+)\+?\s*years?\s+(?:of\s+)?experience", lowered)
        experience_years = int(years_match.group(1)) if years_match else 0
        if any(term in lowered for term in ("frontend", "react", "ui developer")):
            role = "Frontend Engineer"
        elif any(term in lowered for term in ("data engineer", "data engineering", "spark", "airflow")):
            role = "Data Engineer"
        elif any(term in lowered for term in ("machine learning", "ml engineer", "tensorflow", "pytorch")):
            role = "Machine Learning Engineer"
        else:
            role = "Backend Engineer"
        candidates.append({
            "candidate_id": Path(file_info["path"]).stem,
            "name": name,
            "role": role,
            "experience_years": experience_years,
            "skills": skills,
            "location": None,
            "preferences": {},
            "resume_path": file_info["path"],
        })

    return candidates


def main() -> None:
    print("Agentic Profile Matching Chat")
    print("Type 'exit' to quit.")
    session = ConversationSession(
        "Backend Engineer with Python and FastAPI",
        load_sample_candidates(),
    )
    while True:
        query = input("You: ").strip()
        if query.lower() in {"exit", "quit"}:
            break
        print(f"Agent:\n{session.ask(query)}")


if __name__ == "__main__":
    main()
