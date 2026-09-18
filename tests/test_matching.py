from fastapi.testclient import TestClient

from app.main import app
from app.services.matching import match_profiles, rank_candidates
from matching_agent import parse_natural_language_query, screen_candidates, tool_registry


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


def test_match_api_returns_report_and_ranked_candidates():
    client = TestClient(app)

    payload = {
        "job_description": "Backend Engineer with Python, FastAPI, PostgreSQL and API design",
        "candidates": [
            {
                "name": "Aarav",
                "role": "Backend Engineer",
                "experience_years": 5,
                "skills": ["Python", "FastAPI", "PostgreSQL", "Redis"],
                "location": "Bengaluru",
                "preferences": {"remote": True, "industry": "fintech"},
            },
            {
                "name": "Nisha",
                "role": "Backend Engineer",
                "experience_years": 4,
                "skills": ["Python", "FastAPI", "SQL", "Redis"],
                "location": "Bengaluru",
                "preferences": {"remote": True, "industry": "fintech"},
            },
        ],
    }

    response = client.post("/match", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert "report" in data
    assert len(data["matches"]) >= 2


def test_natural_language_query_parses_filters():
    parsed = parse_natural_language_query("Find me candidates with React and 3+ years experience")

    assert parsed["skills"] == ["react"]
    assert parsed["min_experience"] == 3


def test_screening_pipeline_generates_hire_or_no_hire_recommendation():
    candidates = [
        {
            "name": "Alice",
            "role": "Backend Engineer",
            "experience_years": 6,
            "skills": ["Python", "FastAPI", "PostgreSQL", "Redis"],
            "location": "Bengaluru",
            "preferences": {"remote": True, "industry": "fintech"},
        },
        {
            "name": "Bob",
            "role": "Backend Engineer",
            "experience_years": 2,
            "skills": ["JavaScript", "React"],
            "location": "Delhi",
            "preferences": {"remote": False, "industry": "ecommerce"},
        },
    ]

    result = screen_candidates(candidates, "Backend Engineer with Python, FastAPI, and SQL")

    assert "initial_pool" in result
    assert "final_recommendation" in result
    assert result["final_recommendation"]["decision"] in {"hire", "no_hire"}
