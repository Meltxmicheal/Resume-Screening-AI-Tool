# Resume Screening AI

Production-ready AI system for screening and ranking job candidates.

## Project Structure

```
resume-ai/
├── backend/
│   ├── main.py              # FastAPI entrypoint
│   ├── requirements.txt
│   ├── .env.example
│   ├── api/
│   │   └── routes.py        # REST endpoints
│   ├── parser/
│   │   ├── resume_parser.py # PDF/DOCX parsing
│   │   └── jd_parser.py     # Job description parsing
│   ├── nlp/
│   │   └── embeddings.py    # Sentence-transformers
│   ├── engine/
│   │   └── scorer.py        # Weighted scoring engine
│   └── db/
│       └── database.py      # SQLite schema & queries
└── frontend/
    └── index.html           # React-free single-file UI
```

## Setup

### 1. Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env

# Start server
uvicorn main:app --reload --port 8000
```

The first run downloads the `all-MiniLM-L6-v2` model (~90MB).

### 2. Frontend

Open `frontend/index.html` directly in a browser, or serve it:

```bash
cd frontend
python -m http.server 3000
# Then open http://localhost:3000
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/screen` | Upload resumes + JD, get ranked results |
| GET | `/api/v1/session/{id}` | Retrieve previous session results |
| GET | `/health` | Health check |

### POST /api/v1/screen

**Form data:**
- `job_description` (string, min 50 chars)
- `resumes[]` (files, PDF/DOCX, max 5MB each, up to 20)

**Response:**
```json
{
  "session_id": "uuid",
  "total_candidates": 3,
  "job_requirements": {
    "required_skills": ["python", "fastapi"],
    "required_experience": 3.0,
    "required_education": "bachelor"
  },
  "candidates": [
    {
      "rank": 1,
      "name": "Jane Doe",
      "total_score": 82.5,
      "skills_score": 90.0,
      "experience_score": 85.0,
      "semantic_score": 75.0,
      "education_score": 100.0,
      "matched_skills": ["python", "fastapi", "docker"],
      "missing_skills": ["kubernetes"],
      "experience_years": 4.0,
      "experience_gap": 0.0,
      "decision": "Strong Match – Recommend Interview"
    }
  ]
}
```

## Scoring Model

| Component | Weight | Method |
|-----------|--------|--------|
| Skills | 40% | Jaccard overlap vs required skills |
| Experience | 30% | Years ratio (capped at 1.0) |
| Semantic | 20% | Cosine similarity via sentence-transformers |
| Education | 10% | Level mapping (PhD=5, Master=4, Bachelor=3…) |

## Decision Thresholds

| Score | Decision |
|-------|----------|
| ≥75% + skills ≥70% | Strong Match – Recommend Interview |
| ≥55% + skills ≥50% | Moderate Match – Consider for Review |
| ≥35% | Weak Match – Skills Gap Present |
| <35% | Poor Match – Not Recommended |

## Security

- File type validation (PDF/DOCX only)
- Max file size: 5MB per file
- Max files: 20 per request
- Input length validation on JD
- UUID validation on session IDs
- No hardcoded secrets (use .env)
- Raw text truncated to 5000 chars in DB

## Environment Variables

```env
DB_PATH=resume_ai.db          # SQLite database path
ALLOWED_ORIGINS=http://localhost:3000   # CORS origins (comma-separated)
PORT=8000                     # Server port
```
