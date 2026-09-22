# German A1 Intelligent Tutoring System

An AI-powered language tutoring application for German A1 learners, built as part of an HCAI (Human-Centred AI) course project at Otto-von-Guericke University Magdeburg (OVGU), 2026.

## What it does

The app generates personalised German A1 questions, evaluates student answers, and provides step-by-step explanations tailored to the student's exact mistake — not generic feedback. Difficulty adapts automatically based on performance.

**5-step flow:**
1. Student picks a topic (Greetings, Numbers, Articles, Verbs, Sentences)
2. AI generates a fresh A1-level question
3. Student types their answer in the Streamlit chat interface
4. AI explains the specific mistake using Chain-of-Thought reasoning
5. Difficulty adjusts visibly — harder if correct, easier if wrong

## HCAI Design Principles

This project addresses 3 research gaps identified in educational AI literature:

| Principle | Gap addressed | Implementation |
|-----------|--------------|----------------|
| Explainability | Generic feedback doesn't help learners understand mistakes | Chain-of-Thought prompts generate personalised error explanations from the student's exact wrong answer |
| Transparency | Students don't know why difficulty changed | Difficulty level re-stated every prompt — student always sees why it changed |
| Fairness | AI tutors perform inconsistently across student backgrounds | Fairness evaluation tested across South Asian, East Asian, and European student profiles |
| Drift Prevention | LLMs drift from A1 level over long sessions | Difficulty level re-injected with every prompt to prevent alignment drift (Almasi & Kristensen-McLachlan, 2025) |
| Human Control | AI decides everything — student has no agency | Student picks topic, pace, and whether to use hints |

## Tech Stack

| Tool | Purpose |
|------|---------|
| Python | Core application logic |
| Streamlit | Browser-based chat interface |
| OpenAI / Gemini API | Question generation and error explanation |
| SQLite | Student progress and session tracking |
| GitHub | Version control |

## Research Foundation

Grounded in 8 academic papers addressing open gaps in Intelligent Tutoring System (ITS) research:
- Stamper et al. (2024) — 30 years of ITS research, CMU
- Almasi & Kristensen-McLachlan (2025, ACL BEA Workshop) — alignment drift in LLM tutors
- FairAIED survey (2024) — fairness gaps in educational AI

## My Contribution

This was a group course project (Group 21, HCAI, OVGU 2026). My specific contributions:
- Designed the Chain-of-Thought prompting strategy for personalised error explanations
- Implemented the alignment drift prevention mechanism
- Designed and executed the fairness evaluation framework across student profiles
- Led the literature review identifying the 3 research gaps

## How to run

```bash
# Install dependencies
pip install streamlit openai python-dotenv

# Add your API key to .env file
OPENAI_API_KEY=your_key_here

# Run the app
streamlit run app.py
```

> Note: `.env` file with API key required — not included in this repo for security.

## Course

HCAI (Human-Centred Artificial Intelligence) — MSc Data & Knowledge Engineering, OVGU Magdeburg, 2026
