# Agent State Machine

```mermaid
flowchart LR
    START([START]) --> PARSE[Parse JD]
    PARSE --> EXTRACT[Extract Requirements]
    EXTRACT --> SEARCH[Search Resumes]
    SEARCH --> RANK[Rank Candidates]
    RANK --> REPORT[Generate Report]
    REPORT --> REVIEW{Human Feedback?}
    REVIEW -->|New feedback| LOOP[Update Requirements / Reasoning]
    LOOP --> RANK
    REVIEW -->|No feedback| END([END])
```

## State

`MatchingAgentState` stores conversation history, job description, extracted requirements, candidate shortlist, reasoning, generated report, reviewer feedback, review rounds, and whether human review is required.

## Tool boundaries

- Parse and extraction nodes understand the job description.
- Search uses the Milestone 1 filesystem tools and Milestone 2 RAG tool.
- Ranking and reporting produce the shortlist and explanations.
- The human feedback branch supports iterative refinement before completion.
