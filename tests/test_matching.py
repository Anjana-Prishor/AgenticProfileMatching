from app.services.matching import match_profiles, rank_candidates
from matching_agent import tool_registry


def test_agent_exposes_filesystem_and_rag_tools():
    tool_names = set(tool_registry)

    assert "read_file" in tool_names
    assert "list_files" in tool_names
    assert "write_file" in tool_names
    assert "search_in_file" in tool_names
    assert "rag_search" in tool_names


def test_profile_match_scores_strong_fit():
    target = {
        "name": "Aisha",
        "role": "Backend Engineer",
        "experience_years": 5,
        "skills": ["Python", "FastAPI", "PostgreSQL", "Redis"],
        "location": "Bengaluru",
        "preferences": {"remote": True, "industry": "fintech"},
    }
    candidate = {
        "name": "Rohan",
        "role": "Backend Engineer",
        "experience_years": 4,
        "skills": ["Python", "FastAPI", "SQL", "Redis"],
        "location": "Bengaluru",
        "preferences": {"remote": True, "industry": "fintech"},
    }

    score = match_profiles(target, candidate)

    assert 0.75 <= score <= 1.0


def test_rank_candidates_prioritizes_best_matches():
    target = {
        "name": "Aisha",
        "role": "Backend Engineer",
        "experience_years": 5,
        "skills": ["Python", "FastAPI", "PostgreSQL", "Redis"],
        "location": "Bengaluru",
        "preferences": {"remote": True, "industry": "fintech"},
    }
    candidates = [
        {
            "name": "Rohan",
            "role": "Frontend Engineer",
            "experience_years": 2,
            "skills": ["JavaScript", "React"],
            "location": "Delhi",
            "preferences": {"remote": False, "industry": "ecommerce"},
        },
        {
            "name": "Nisha",
            "role": "Backend Engineer",
            "experience_years": 4,
            "skills": ["Python", "FastAPI", "SQL", "Redis"],
            "location": "Bengaluru",
            "preferences": {"remote": True, "industry": "fintech"},
        },
        {
            "name": "Kabir",
            "role": "Data Engineer",
            "experience_years": 7,
            "skills": ["Python", "Spark", "Airflow", "SQL"],
            "location": "Pune",
            "preferences": {"remote": True, "industry": "fintech"},
        },
    ]

    ranked = rank_candidates(target, candidates)

    assert ranked[0]["name"] == "Nisha"
    assert ranked[1]["name"] == "Kabir"
    assert ranked[2]["name"] == "Rohan"
