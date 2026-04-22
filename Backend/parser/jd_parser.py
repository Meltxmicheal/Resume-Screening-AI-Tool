import re


def parse_jd(job_description: str) -> dict:

    text = job_description.lower()

    # -------- SKILLS --------
    skills = re.findall(
        r'\b(python|java|javascript|react|angular|node|sql|aws|docker|kubernetes|'
        r'machine learning|deep learning|nlp|tensorflow|pytorch|excel|communication)\b',
        text
    )

    required_skills = list(set(skills))

    # -------- EXPERIENCE --------
    exp_match = re.search(r'(\d+)\+?\s*years?', text)
    required_experience = int(exp_match.group(1)) if exp_match else 0

    # -------- EDUCATION --------
    if "phd" in text:
        edu = "phd"
    elif "master" in text or "mba" in text:
        edu = "master"
    elif "bachelor" in text or "b.e" in text or "btech" in text:
        edu = "bachelor"
    else:
        edu = "any"

    return {
        "required_skills": required_skills,
        "required_experience": required_experience,
        "required_education_label": edu
    }