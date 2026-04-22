import os
import uuid
import json
from typing import List
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import JSONResponse, FileResponse
import aiosqlite

from db.database import get_db
from parser.resume_parser import parse_resume
from parser.jd_parser import parse_jd
from engine.scorer import score_candidate

router = APIRouter()

MAX_FILE_SIZE = 5 * 1024 * 1024
ALLOWED_EXTENSIONS = {"pdf", "docx"}
UPLOAD_DIR = "uploads"


def validate_file(file: UploadFile):
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"File type not allowed: {file.filename}. Use PDF or DOCX.")


@router.post("/screen")
async def screen_resumes(
    job_description: str = Form(..., min_length=50, max_length=10000),
    resumes: List[UploadFile] = File(...),
    top_n: int = Form(25),
    db: aiosqlite.Connection = Depends(get_db)
):
    if not resumes or len(resumes) > 20:
        raise HTTPException(400, "Upload 1-20 resumes.")

    if top_n <= 0 or top_n > 100:
        top_n = 25

    for f in resumes:
        validate_file(f)

    jd = parse_jd(job_description)

    first_line = job_description.split("\n")[0].split(".")[0]
    roles = [r.strip().lower() for r in first_line.split(",") if len(r.strip()) > 2]

    session_id = str(uuid.uuid4())
    await db.execute(
        "INSERT INTO sessions (id, job_description) VALUES (?, ?)",
        (session_id, job_description)
    )

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    results = []

    for upload in resumes:
        raw = await upload.read()

        if len(raw) > MAX_FILE_SIZE:
            raise HTTPException(400, f"File {upload.filename} exceeds 5MB limit.")

        # Save file to disk so it can be downloaded later
        file_path = os.path.join(UPLOAD_DIR, upload.filename)
        with open(file_path, "wb") as f:
            f.write(raw)

        try:
            resume = parse_resume(raw, upload.filename)
        except Exception:
            continue

        if not resume.get("raw_text") or len(resume["raw_text"].strip()) < 20:
            continue

        score = score_candidate(resume, jd)

        text_lower = resume["raw_text"].lower()
        role_match_count = sum(1 for role in roles if role in text_lower)
        role_score = round((role_match_count / len(roles)) * 100, 1) if roles else 0.0

        total_score = round(
            (score["skills_score"] * 0.35) +
            (score["experience_score"] * 0.25) +
            (score["semantic_score"] * 0.20) +
            (score["education_score"] * 0.10) +
            (role_score * 0.10),
            1
        )

        if total_score >= 75 and score["skills_score"] >= 70:
            decision = "Strong Match - Recommend Interview"
        elif total_score >= 55 and score["skills_score"] >= 50:
            decision = "Moderate Match - Consider for Review"
        elif total_score >= 35:
            decision = "Weak Match - Skills Gap Present"
        else:
            decision = "Poor Match - Not Recommended"

        candidate_id = str(uuid.uuid4())
        score_id = str(uuid.uuid4())

        # Store file_path in filename column so download endpoint can find it
        await db.execute(
            "INSERT INTO candidates (id, session_id, filename, name, email, phone, raw_text) VALUES (?,?,?,?,?,?,?)",
            (candidate_id, session_id, file_path,
             resume["name"], resume["email"], resume["phone"], resume["raw_text"])
        )

        await db.execute(
            """INSERT INTO scores
               (id, candidate_id, session_id, skills_score, experience_score, semantic_score,
                education_score, total_score, matched_skills, missing_skills,
                experience_years, required_experience, education_level, decision)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (score_id, candidate_id, session_id,
             score["skills_score"], score["experience_score"],
             score["semantic_score"], score["education_score"],
             total_score,
             json.dumps(score["matched_skills"]),
             json.dumps(score["missing_skills"]),
             score["experience_years"], score["required_experience"],
             score["education_label"], decision)
        )

        results.append({
            "candidate_id": candidate_id,
            "filename": upload.filename,
            "name": resume["name"],
            "email": resume["email"],
            "total_score": total_score,
            "skills_score": score["skills_score"],
            "experience_score": score["experience_score"],
            "semantic_score": score["semantic_score"],
            "education_score": score["education_score"],
            "role_score": role_score,
            "matched_skills": score["matched_skills"],
            "missing_skills": score["missing_skills"],
            "experience_years": score["experience_years"],
            "required_experience": jd["required_experience"],
            "experience_gap": score["experience_gap"],
            "education_label": score["education_label"],
            "decision": decision,
        })

    await db.commit()

    ranked = sorted(results, key=lambda x: x["total_score"], reverse=True)[:top_n]
    for i, r in enumerate(ranked):
        r["rank"] = i + 1

    return JSONResponse({
        "session_id": session_id,
        "total_candidates": len(ranked),
        "job_requirements": {
            "required_skills": jd["required_skills"],
            "required_experience": jd["required_experience"],
            "required_education": jd["required_education_label"],
            "roles_detected": roles,
        },
        "candidates": ranked,
    })


@router.get("/download/{candidate_id}")
async def download_resume(candidate_id: str, db: aiosqlite.Connection = Depends(get_db)):
    try:
        uuid.UUID(candidate_id)
    except ValueError:
        raise HTTPException(400, "Invalid candidate ID.")

    async with db.execute(
        "SELECT filename FROM candidates WHERE id = ?",
        (candidate_id,)
    ) as cursor:
        row = await cursor.fetchone()

    if not row:
        raise HTTPException(404, "Candidate not found.")

    file_path = row[0]

    if not os.path.exists(file_path):
        raise HTTPException(404, f"File not found on disk: {os.path.basename(file_path)}")

    return FileResponse(
        path=file_path,
        filename=os.path.basename(file_path),
        media_type="application/octet-stream"
    )


@router.get("/session/{session_id}")
async def get_session(session_id: str, db: aiosqlite.Connection = Depends(get_db)):
    try:
        uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(400, "Invalid session ID.")

    async with db.execute(
        """SELECT c.id, c.filename, c.name, c.email,
                  s.total_score, s.skills_score, s.experience_score,
                  s.semantic_score, s.education_score,
                  s.matched_skills, s.missing_skills,
                  s.experience_years, s.required_experience,
                  s.education_level, s.decision
           FROM candidates c JOIN scores s ON c.id = s.candidate_id
           WHERE c.session_id = ?
           ORDER BY s.total_score DESC""",
        (session_id,)
    ) as cursor:
        rows = await cursor.fetchall()

    if not rows:
        raise HTTPException(404, "Session not found.")

    candidates = []
    for i, row in enumerate(rows):
        candidates.append({
            "rank": i + 1,
            "candidate_id": row[0],
            "filename": os.path.basename(row[1]),
            "name": row[2],
            "email": row[3],
            "total_score": row[4],
            "skills_score": row[5],
            "experience_score": row[6],
            "semantic_score": row[7],
            "education_score": row[8],
            "matched_skills": json.loads(row[9] or "[]"),
            "missing_skills": json.loads(row[10] or "[]"),
            "experience_years": row[11],
            "required_experience": row[12],
            "education_label": row[13],
            "decision": row[14],
        })

    return {"session_id": session_id, "candidates": candidates}