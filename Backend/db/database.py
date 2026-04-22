import aiosqlite
import os

DB_PATH = os.getenv("DB_PATH", "resume_ai.db")


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:

        await db.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            job_description TEXT
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS candidates (
            id TEXT PRIMARY KEY,
            session_id TEXT,
            filename TEXT,
            name TEXT,
            email TEXT,
            phone TEXT,
            raw_text TEXT
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS scores (
            id TEXT PRIMARY KEY,
            candidate_id TEXT,
            session_id TEXT,
            skills_score REAL,
            experience_score REAL,
            semantic_score REAL,
            education_score REAL,
            total_score REAL,
            matched_skills TEXT,
            missing_skills TEXT,
            experience_years REAL,
            required_experience REAL,
            education_level TEXT,
            decision TEXT
        )
        """)

        await db.commit()


async def get_db():
    db = await aiosqlite.connect(DB_PATH)
    try:
        yield db
    finally:
        await db.close()