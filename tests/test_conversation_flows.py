from chat_interface import ConversationSession, default_candidates


JOB_DESCRIPTION = "Backend Engineer with Python and FastAPI"


def session() -> ConversationSession:
    return ConversationSession(JOB_DESCRIPTION, default_candidates())


def test_flow_find_candidates_by_skill_and_experience():
    answer = session().ask("Find candidates with Python and 4+ years experience")

    assert "Aarav" in answer
    assert "Nisha" in answer
    assert "Rohan" not in answer


def test_flow_compare_top_matches():
    answer = session().ask("Compare the top 3 matches side by side")

    assert "Side-by-side comparison" in answer
    assert "Aarav" in answer
    assert "Nisha" in answer


def test_flow_explain_ranking():
    answer = session().ask("Why did Aarav rank higher than Rohan?")

    assert "Ranking explanation" in answer
    assert "strengths" in answer
    assert "gaps" in answer


def test_flow_generate_interview_questions():
    answer = session().ask("Generate interview questions for the top candidate")

    assert "Interview questions" in answer
    assert "trade-offs" in answer


def test_flow_iteratively_refines_requirements():
    active_session = session()
    first_answer = active_session.ask("Find candidates with Python")
    second_answer = active_session.ask("Now find candidates with React")

    assert "Aarav" in first_answer
    assert "Rohan" in second_answer
    assert "Aarav" not in second_answer
    assert len(active_session.history) == 4


def test_minimum_experience_does_not_penalize_more_experience():
    answer = session().ask("Find candidates with Python and 4+ years experience")

    assert answer.index("Aarav") < answer.index("Nisha")
    assert "Aarav" in answer and "score=1.0" in answer
