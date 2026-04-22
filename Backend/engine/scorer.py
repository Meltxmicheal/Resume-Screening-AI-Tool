import math
from nlp.embeddings import get_similarity


def score_candidate(resume: dict, jd: dict) -> dict:

    # -------- SKILLS --------
    resume_skills = set(resume.get("skills", []))
    jd_skills = set(jd.get("required_skills", []))

    matched = list(resume_skills & jd_skills)
    missing = list(jd_skills - resume_skills)

    skill_score = int((len(matched) / (len(jd_skills) or 1)) * 100)

    # -------- EXPERIENCE --------
    experience_years = resume.get("experience_years", 0)
    required_exp = jd.get("required_experience", 0)

    experience_score = int(min((experience_years / (required_exp or 1)) * 100, 100))
    experience_gap = max(required_exp - experience_years, 0)

    # -------- SEMANTIC --------
    semantic_score = int(
        get_similarity(resume.get("raw_text", ""), jd.get("raw_text", "")) * 100
    )

    # -------- EDUCATION --------
    edu_score = resume.get("education_level", 0) * 20  # scale 0–100

    return {
        "skills_score": skill_score,
        "experience_score": experience_score,
        "semantic_score": semantic_score,
        "education_score": edu_score,
        "matched_skills": matched,
        "missing_skills": missing,
        "experience_years": experience_years,
        "required_experience": required_exp,
        "experience_gap": experience_gap,
        "education_label": resume.get("education_label", "unknown"),
    }