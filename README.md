# Agentic Profile Matching

A LangGraph-based agent for matching job descriptions against candidate profiles using a combination of filesystem tools, RAG-based resume retrieval, and ranking logic.

## Overview

This project builds an agentic hiring workflow that:

- parses a job description,
- extracts must-have and nice-to-have requirements,
- searches available resumes using a retrieval pipeline,
- ranks candidates based on skill and experience fit,
- generates a match report,
- supports human feedback and iterative refinement,
- produces a final hire/no-hire recommendation for shortlisted candidates.

## Project Structure

- `matching_agent.py` — LangGraph workflow and tool registry
- `app/main.py` — FastAPI backend with endpoints for matching and resume ingestion
- `app/services/matching.py` — candidate scoring and ranking logic
- `demo_agent.py` — demo workflow using the actual resume corpus
- `chat_interface.py` — interactive CLI chat interface
- `tests/test_matching.py` — automated verification for scoring, API, and screening logic
- `tests/test_conversation_flows.py` — five conversational test scenarios
- `docs/state_machine.md` — visual LangGraph state-machine diagram
- `docs/demo_video_script.md` — 5-6 minute recording script
- `milestone1_filesystem_assistant/` — filesystem tools from Milestone 1
- `milestone2_rag_profile_matching/` — resume RAG pipeline and sample resumes from Milestone 2

## Architecture

The core workflow is:

START → Parse JD → Extract Requirements → Search Resumes → Rank Candidates → Generate Report → Human Feedback Loop → END

The agent tracks:

- conversation history,
- job requirement understanding,
- shortlist of candidates,
- match reasoning,
- report generation status,
- human review feedback.

## Tools Exposed to the Agent

- File system tools:
  - `read_file`
  - `list_files`
  - `write_file`
  - `search_in_file`
- RAG search tool:
  - `rag_search`
- Matching tools:
  - `extract_requirements`
  - `compare_candidates`
  - `generate_interview_questions`
  - `parse_natural_language_query`
  - `screen_candidates`

## API Endpoints

### Health check

- `GET /health`

### Candidate matching

- `POST /match`

Payload example:

```json
{
  "job_description": "Backend Engineer with Python, FastAPI, PostgreSQL and API design",
  "candidates": [
    {
      "name": "Aarav",
      "role": "Backend Engineer",
      "experience_years": 5,
      "skills": ["Python", "FastAPI", "PostgreSQL", "Redis"],
      "location": "Bengaluru",
      "preferences": {"remote": true, "industry": "fintech"}
    }
  ]
}
```

### Resume ingestion

- `POST /ingest-resumes`

Payload:

```json
{
  "directory": "C:/path/to/resume/folder"
}
```

### RAG resume search

- `POST /rag-search`

Payload:

```json
{
  "query": "Python backend engineer",
  "directory": "./sample_resumes",
  "limit": 5
}
```

## Matching Logic

The matching service computes a score between 0 and 1 using:

- skill overlap,
- role match,
- location fit,
- remote preference alignment,
- industry preference alignment,
- experience closeness.

The score is then used to rank candidates from strongest to weakest match.

## Natural Language Support

The agent can parse queries like:

- "Find me candidates with React and 3+ years experience"
- "Compare the top 3 matches side by side"
- "Why did John rank higher than Jane?"

This is handled by the query parser and the screening pipeline.

## Multi-Round Screening

The screening flow includes:

1. initial pool selection,
2. deep review of top shortlisted candidates,
3. final recommendation with hire/no-hire decision.

Each shortlisted candidate also gets explainability details: strengths, gaps, and improvement suggestions.

## Running the Project

### Install dependencies

```bash
python -m pip install -e .[dev]
```

### Run tests

```bash
python -m pytest -q
```

### Run the demo

```bash
python demo_agent.py
```

### Run the chat interface

```bash
python chat_interface.py
```

The CLI supports candidate searches, requirement refinement, side-by-side comparison, ranking explanations, and interview-question generation. Type `exit` to quit.

### Run the backend

```bash
uvicorn app.main:app --reload
```

## Verification

The project is currently verified by automated tests:

- matching logic tests,
- ranking tests,
- API contract tests,
- natural-language parsing tests,
- multi-round screening tests,
- five conversational interaction flows.

## Submission Materials

- LangGraph implementation: `matching_agent.py`
- State-machine diagram: `docs/state_machine.md`
- Chat interface: `chat_interface.py`
- Conversation scenarios: `tests/test_conversation_flows.py`
- Demo recording guide: `docs/demo_video_script.md`

## Future Enhancements

- integrate a richer LLM-based planner for real-time conversational reasoning,
- add support for PDF/DOCX resume ingestion at scale,
- extend comparison explanations for hiring managers,
- store session history in a database.

## Summary

This project combines agentic workflow orchestration, retrieval-augmented resume search, and hiring intelligence into a single backend and agent system designed for profile matching and candidate ranking.
