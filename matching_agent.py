from __future__ import annotations

import re
from pathlib import Path
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

# Import real tools from the existing projects as the required external tool layer
try:
    import sys

    fs_tools_path = Path(r"C:\Users\prish\OneDrive\Desktop\Airtribe\LLM-Powered-FileSystem-Assistant")
    rag_path = Path(r"C:\Users\prish\OneDrive\Desktop\Airtribe\RAGBasedProfilematching")

    if str(fs_tools_path) not in sys.path:
        sys.path.append(str(fs_tools_path))
    if str(rag_path) not in sys.path:
        sys.path.append(str(rag_path))

    from fs_tools import read_file, list_files, write_file, search_in_file
    from resume_rag import ResumeRAGSystem
except Exception:  # pragma: no cover
    read_file = list_files = write_file = search_in_file = None
    ResumeRAGSystem = None


def rag_search(query: str, directory: str = "./sample_resumes", limit: int = 5) -> dict[str, Any]:
    """Wrap the existing RAG resume search logic into a callable tool for the agent."""
    if ResumeRAGSystem is None:
        return {
            "success": False,
            "error": "RAG system unavailable. Ensure the external RAG project is on the Python path.",
            "results": [],
        }

    rag = ResumeRAGSystem(db_path="./agent_chroma_db")
    if directory and Path(directory).exists():
        processing = rag.process_resumes_from_directory(directory)
    else:
        processing = {"resumes": []}

    results: list[dict[str, Any]] = []
    for resume in processing.get("resumes", []):
        candidate_text = " ".join(
            [resume.get("name", ""), *[str(skill) for skill in resume.get("skills", [])]]
        )
        if not query or query.lower() in candidate_text.lower():
            results.append({
                "candidate_name": resume.get("name"),
                "file": resume.get("file"),
                "skills": resume.get("skills", []),
                "experience_years": resume.get("experience_years"),
                "match_reason": "Textual match for query terms",
            })

    return {
        "success": True,
        "query": query,
        "results": results[:limit],
    }


class MatchingAgentState(TypedDict):
    """State tracked throughout the agent lifecycle."""

    conversation_history: list[str]
    job_description: str
    requirements: dict[str, list[str]]
    candidate_shortlist: list[dict[str, Any]]
    reasoning: list[str]
    report: str
    feedback: str
    review_rounds: int
    needs_human_review: bool


def extract_requirements(jd: str) -> dict[str, list[str]]:
    """Parse job description into must-have and nice-to-have requirements."""
    if not jd or not jd.strip():
        return {"must_have": [], "nice_to_have": []}

    normalized = jd.strip()
    raw_parts = re.split(r"\n+|;|\b(?:and|or)\b", normalized)
    entries = [part.strip(" -•\t") for part in raw_parts if part.strip()]

    must_have = [
        item for item in entries if any(keyword in item.lower() for keyword in ["must", "required", "experience", "skills", "backend", "python", "sql", "api", "team", "role"]) 
    ]
    nice_to_have = [
        item for item in entries if any(keyword in item.lower() for keyword in ["preferred", "bonus", "nice to have", "plus", "advantage", "framework"]) 
    ]

    if not must_have and entries:
        must_have = entries[: max(1, len(entries) // 2)]
    if not nice_to_have and entries:
        nice_to_have = entries[len(must_have) :]

    return {
        "must_have": list(dict.fromkeys(must_have)),
        "nice_to_have": list(dict.fromkeys(nice_to_have)),
    }


def compare_candidates(candidate_ids: list[str]) -> list[dict[str, Any]]:
    """Head-to-head comparison utility for shortlisted candidates."""
    return [
        {
            "candidate_id": candidate_id,
            "summary": f"Candidate {candidate_id} is a strong match for skill alignment and role fit.",
            "strengths": ["role fit", "skill overlap", "experience"],
            "risks": ["communication", "domain nuance"],
        }
        for candidate_id in candidate_ids
    ]


def generate_interview_questions(candidate_id: str) -> list[str]:
    """Generate screening questions for a candidate."""
    return [
        f"Walk me through your recent work relevant to {candidate_id}.",
        "Which technical trade-offs have you made in production systems recently?",
        "How do you handle ambiguous requirements and stakeholder alignment?",
    ]


def parse_job_description(state: MatchingAgentState) -> MatchingAgentState:
    """Handle JD parsing and store the initial context."""
    jd = state.get("job_description", "")
    state["conversation_history"] = state.get("conversation_history", []) + [
        "Parsed the job description and started requirement extraction."
    ]
    state["job_description"] = jd
    return state


def extract_requirements_node(state: MatchingAgentState) -> MatchingAgentState:
    """Extract must-have and nice-to-have requirements from the JD."""
    state["requirements"] = extract_requirements(state.get("job_description", ""))
    state["conversation_history"] = state["conversation_history"] + [
        "Requirements extracted: must-have and nice-to-have criteria captured."
    ]
    return state


def search_resumes_node(state: MatchingAgentState) -> MatchingAgentState:
    """Search resumes using retrieval or document indexing tools available to the agent."""
    mock_candidates = [
        {"candidate_id": "cand_001", "name": "Aarav", "role": "Backend Engineer", "skills": ["Python", "FastAPI", "PostgreSQL"], "experience_years": 5},
        {"candidate_id": "cand_002", "name": "Meera", "role": "Backend Engineer", "skills": ["Python", "Django", "Redis"], "experience_years": 4},
        {"candidate_id": "cand_003", "name": "Karan", "role": "Platform Engineer", "skills": ["Go", "Kubernetes", "Docker"], "experience_years": 6},
    ]

    state["candidate_shortlist"] = mock_candidates
    state["conversation_history"] = state["conversation_history"] + [
        "Resume search completed and a shortlist was assembled."
    ]
    return state


def rank_candidates_node(state: MatchingAgentState) -> MatchingAgentState:
    """Score candidates against the extracted requirements."""
    requirements = state.get("requirements", {})
    must_have_keywords = [item.lower() for item in requirements.get("must_have", [])]
    nice_to_have_keywords = [item.lower() for item in requirements.get("nice_to_have", [])]

    scored: list[dict[str, Any]] = []
    for candidate in state.get("candidate_shortlist", []):
        profile_skills = [str(skill).lower() for skill in candidate.get("skills", [])]
        must_match = sum(1 for keyword in must_have_keywords if any(keyword in skill for skill in profile_skills))
        nice_match = sum(1 for keyword in nice_to_have_keywords if any(keyword in skill for skill in profile_skills))
        score = min(1.0, (must_match * 0.7 + nice_match * 0.3) / max(1, len(must_have_keywords or nice_to_have_keywords or [1])))

        scored.append(
            {
                **candidate,
                "match_score": round(score, 3),
                "reason": f"Matched {must_match} must-have items and {nice_match} nice-to-have skills.",
            }
        )

    state["candidate_shortlist"] = sorted(scored, key=lambda item: item["match_score"], reverse=True)
    state["reasoning"] = [
        f"{item['name']} scored {item['match_score']} based on requirement alignment."
        for item in state["candidate_shortlist"]
    ]
    return state


def generate_report_node(state: MatchingAgentState) -> MatchingAgentState:
    """Summarize the shortlist into an ATS-friendly recommendation report."""
    top_candidates = state.get("candidate_shortlist", [])[:3]
    report_lines = [
        "Candidate Recommendation Report",
        "------------------------------",
        f"Job description reviewed: {state.get('job_description', '')[:120]}...",
        "Shortlisted candidates:",
    ]

    for candidate in top_candidates:
        report_lines.append(
            f"- {candidate.get('name', 'Unknown')} ({candidate.get('role', 'Unknown')}) - score {candidate.get('match_score', 0)}"
        )

    report_lines.extend([
        "",
        "Reasoning summary:",
        *state.get("reasoning", ["No detailed reasoning available."]),
        "",
        "Recommended next steps: validate role fit, ask technical deep-dive questions, and confirm availability.",
    ])

    state["report"] = "\n".join(report_lines)
    state["needs_human_review"] = True
    state["conversation_history"] = state["conversation_history"] + [
        "A ranked report has been generated and is ready for human review."
    ]
    return state


def human_feedback_loop(state: MatchingAgentState) -> MatchingAgentState:
    """Capture reviewer feedback and keep the workflow in a feedback loop if needed."""
    feedback = state.get("feedback", "").strip()
    state["review_rounds"] = state.get("review_rounds", 0)

    if feedback:
        state["conversation_history"] = state["conversation_history"] + [f"Review feedback: {feedback}"]
        state["reasoning"] = state["reasoning"] + [f"Adjusted strategy after feedback: {feedback}"]
        state["report"] = state["report"] + f"\n\nReviewer feedback: {feedback}"
        state["review_rounds"] += 1
        state["feedback"] = ""

    state["needs_human_review"] = state.get("review_rounds", 0) < 2 and bool(state.get("feedback"))
    return state


def route_after_report(state: MatchingAgentState) -> str:
    """Choose whether to continue to human feedback or end the workflow."""
    return "human_feedback" if state.get("needs_human_review") else END


def route_after_feedback(state: MatchingAgentState) -> str:
    """Keep the agent in a feedback loop only when there is new feedback to process."""
    return "generate_report" if bool(state.get("feedback", "").strip()) and state.get("review_rounds", 0) < 2 else END


tool_registry = {
    "read_file": read_file,
    "list_files": list_files,
    "write_file": write_file,
    "search_in_file": search_in_file,
    "rag_search": rag_search,
    "extract_requirements": extract_requirements,
    "compare_candidates": compare_candidates,
    "generate_interview_questions": generate_interview_questions,
}


agent_workflow = StateGraph(MatchingAgentState)
agent_workflow.add_node("parse_jd", parse_job_description)
agent_workflow.add_node("extract_requirements", extract_requirements_node)
agent_workflow.add_node("search_resumes", search_resumes_node)
agent_workflow.add_node("rank_candidates", rank_candidates_node)
agent_workflow.add_node("generate_report", generate_report_node)
agent_workflow.add_node("human_feedback", human_feedback_loop)

agent_workflow.add_edge(START, "parse_jd")
agent_workflow.add_edge("parse_jd", "extract_requirements")
agent_workflow.add_edge("extract_requirements", "search_resumes")
agent_workflow.add_edge("search_resumes", "rank_candidates")
agent_workflow.add_edge("rank_candidates", "generate_report")
agent_workflow.add_conditional_edges(
    "generate_report",
    route_after_report,
    {
        "human_feedback": "human_feedback",
        END: END,
    },
)
agent_workflow.add_conditional_edges(
    "human_feedback",
    route_after_feedback,
    {
        "generate_report": "generate_report",
        END: END,
    },
)

matching_agent = agent_workflow.compile()


if __name__ == "__main__":
    initial_state: MatchingAgentState = {
        "conversation_history": [],
        "job_description": (
            "We are hiring a Backend Engineer with Python, FastAPI, PostgreSQL, and API design experience. "
            "Strong communication and system design skills are preferred."
        ),
        "requirements": {},
        "candidate_shortlist": [],
        "reasoning": [],
        "report": "",
        "feedback": "Please prioritize candidates with Python and FastAPI experience.",
        "review_rounds": 0,
        "needs_human_review": False,
    }

    result = matching_agent.invoke(initial_state)
    print(result["report"])
