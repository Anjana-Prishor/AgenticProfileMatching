from __future__ import annotations


def _normalize_skills(skills):
    return {skill.lower().strip() for skill in (skills or []) if skill and skill.strip()}


def match_profiles(target, candidate):
    """Return a compatibility score between 0 and 1 for a target and candidate profile."""
    if not target or not candidate:
        return 0.0

    target_skills = _normalize_skills(target.get("skills", []))
    candidate_skills = _normalize_skills(candidate.get("skills", []))
    shared_skills = target_skills & candidate_skills
    total_target_skills = len(target_skills) or 1
    skill_similarity = len(shared_skills) / total_target_skills

    role_match = 1.0 if target.get("role") == candidate.get("role") else 0.0
    location_match = 1.0 if target.get("location") == candidate.get("location") else 0.0
    remote_match = 1.0 if target.get("preferences", {}).get("remote") == candidate.get("preferences", {}).get("remote") else 0.0
    industry_match = 1.0 if target.get("preferences", {}).get("industry") == candidate.get("preferences", {}).get("industry") else 0.0

    exp_gap = abs(int(target.get("experience_years", 0)) - int(candidate.get("experience_years", 0)))
    experience_score = max(0.0, 1.0 - (exp_gap / 10.0))

    score = (
        0.4 * skill_similarity
        + 0.2 * role_match
        + 0.1 * location_match
        + 0.1 * remote_match
        + 0.1 * industry_match
        + 0.1 * experience_score
    )
    return round(max(0.0, min(1.0, score)), 3)


def rank_candidates(target, candidates):
    """Return candidates sorted by best match descending."""
    scored = [
        {**candidate, "match_score": match_profiles(target, candidate)}
        for candidate in (candidates or [])
    ]
    return sorted(scored, key=lambda item: item["match_score"], reverse=True)
