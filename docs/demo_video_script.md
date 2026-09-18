# Demo Video Script: 5-6 Minutes

## 0:00-0:30: Introduction

State the problem: recruiters need to match a job description against many resumes while retaining explainability. Show the single repository and identify the three consolidated projects.

## 0:30-1:30: Architecture

Open `matching_agent.py`. Show `MatchingAgentState`, the LangGraph nodes, and the workflow:

START -> Parse JD -> Extract Requirements -> Search Resumes -> Rank Candidates -> Generate Report -> Human Feedback Loop -> END.

Open `docs/state_machine.md` to show the visual diagram.

## 1:30-2:15: Tools

Show the `tool_registry`. Explain that filesystem tools come from `milestone1_filesystem_assistant`, while resume ingestion and retrieval come from `milestone2_rag_profile_matching`. Point to `job_descriptions/current_job_description.txt` and the sample resume folder.

## 2:15-3:15: End-to-end demo

Run:

```powershell
python demo_agent.py
```

Show the job requirements and ranked candidates. Explain that changing the text file changes the job criteria without changing Python code.

## 3:15-4:00: Chat interface

Run:

```powershell
python chat_interface.py
```

Demonstrate these requests:

1. `Find candidates with Python and 4+ years experience`
2. `Compare the top 3 matches side by side`
3. `Why did Aarav rank higher than Rohan?`
4. `Generate interview questions`
5. `Find candidates with React`

Explain that the session preserves history and re-ranks after new requirements.

## 4:00-4:45: Advanced screening and explainability

Show `screen_candidates` in `matching_agent.py`. Explain the initial pool, deep review, final hire/no-hire recommendation, strengths, gaps, and improvement suggestions.

## 4:45-5:30: Testing

Run:

```powershell
python -m pytest -q
```

Explain that the suite covers architecture tools, ranking, API behavior, natural-language filters, chat flows, and multi-round screening.

## 5:30-6:00: Closing

Summarize: the project combines LangGraph orchestration, filesystem tools, RAG resume search, conversational refinement, multi-round screening, and explainable recommendations in one submission repository.
