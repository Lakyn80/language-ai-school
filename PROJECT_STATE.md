# LANGUAGE AI SCHOOL

Goal:
AI language-learning platform based on:
- real-life situations
- movie-style worlds
- CEFR levels A1–C1
- no traditional grammar lessons

## DONE

- Dockerized backend
- FastAPI app factory
- Modular architecture
- RAG engine (FAISS)
- Difficulty engine (A1–C1)
- Scene system (DB + JSON)
- World system (RAG titles)
- Cache layer
- CI (GitHub Actions)

backend/
├── app/
│   ├── api/
│   ├── core/
│   ├── modules/
│   │   ├── lessons/
│   │   ├── scenes/
│   │   ├── rag/
│   │   ├── titles/
│   │   └── health/
│   └── pedagogy/
│       ├── levels.py
│       ├── difficulty_engine.py
│       └── languages/

- No grammar lessons
- Grammar is implicit only
- Learning = situations + stories
- Same scene works for A1 → C1
- Language complexity is enforced automatically

Worlds:
- secret_agent (James Bond–style)
- fantasy_school (Harry Potter–style)
- sci_fi (Avatar–style)
- police
- hospital
- IT_office

Each world contains:
- characters
- tone
- locations
- allowed actions

Story modes:
- strict      (CEFR-only)
- story       (light dramatization)
- cinematic   (dialogues + emotion)

Grammar is planned as a separate module.
Lessons must not depend on grammar implementation.
Grammar can be added later without breaking existing lessons.

DO NOT:
- remove Docker
- hardcode CEFR rules
- duplicate scene logic
- mix languages
- bypass difficulty engine

CURRENT STEP:
Implement story mode engine (strict / story / cinematic)
