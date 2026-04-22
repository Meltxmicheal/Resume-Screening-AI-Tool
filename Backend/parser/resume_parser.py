import re
import io
from typing import Optional, List
import pdfplumber
from docx import Document


EDUCATION_KEYWORDS = {
    "phd": 5, "doctorate": 5, "ph.d": 5,
    "master": 4, "msc": 4, "mba": 4, "m.s": 4, "m.e": 4,
    "bachelor": 3, "bsc": 3, "b.e": 3, "b.tech": 3, "b.s": 3,
    "associate": 2, "diploma": 1, "high school": 1
}

SKILL_PATTERNS = re.compile(
    r'\b(python|java|javascript|typescript|react|angular|vue|node\.?js|'
    r'sql|postgresql|mysql|mongodb|redis|aws|gcp|azure|docker|kubernetes|'
    r'git|linux|html|css|rest|graphql|fastapi|django|flask|spring|'
    r'machine learning|deep learning|nlp|tensorflow|pytorch|scikit.learn|'
    r'pandas|numpy|spark|hadoop|kafka|elasticsearch|ci/cd|devops|'
    r'c\+\+|c#|golang|rust|ruby|php|scala|swift|kotlin|r\b|matlab|'
    r'tableau|power bi|excel|agile|scrum|jira|jenkins|terraform|ansible)\b',
    re.IGNORECASE
)


def extract_text_from_pdf(file_bytes: bytes) -> str:
    text = ""
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text


def extract_text_from_docx(file_bytes: bytes) -> str:
    doc = Document(io.BytesIO(file_bytes))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


def extract_name(text: str) -> str:
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    for line in lines[:5]:
        if (len(line.split()) in [2, 3] and
                not any(c.isdigit() for c in line) and
                not any(k in line.lower() for k in ["email", "phone", "address", "@", "http"])):
            return line.title()
    return "Unknown"


def extract_email(text: str) -> Optional[str]:
    match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
    return match.group() if match else None


def extract_phone(text: str) -> Optional[str]:
    match = re.search(r'[\+]?[(]?[0-9]{1,4}[)]?[-\s\.]?[(]?[0-9]{1,3}[)]?[-\s\.]?[0-9]{3,4}[-\s\.]?[0-9]{3,4}', text)
    return match.group() if match else None


def extract_skills(text: str) -> List[str]:
    found = set(m.group().lower() for m in SKILL_PATTERNS.finditer(text))
    return sorted(list(found))


def extract_experience_years(text: str) -> float:
    patterns = [
        r'(\d+)\+?\s*years?\s*(?:of\s+)?(?:experience|exp)',
        r'experience[:\s]+(\d+)\+?\s*years?',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return float(match.group(1))

    # Count year ranges in work history
    year_ranges = re.findall(r'(20\d{2}|19\d{2})\s*[-–]\s*(20\d{2}|19\d{2}|present|current)', text, re.IGNORECASE)
    total = 0.0
    for start, end in year_ranges:
        try:
            s = int(start)
            e = 2024 if end.lower() in ("present", "current") else int(end)
            if 1980 <= s <= 2024 and s <= e:
                total += e - s
        except ValueError:
            continue
    return min(total, 30.0)


def extract_education_level(text: str) -> tuple[str, int]:
    text_lower = text.lower()
    best_level = ("none", 0)
    for keyword, level in EDUCATION_KEYWORDS.items():
        if keyword in text_lower and level > best_level[1]:
            best_level = (keyword, level)
    return best_level


def parse_resume(file_bytes: bytes, filename: str) -> dict:
    ext = filename.rsplit(".", 1)[-1].lower()
    if ext == "pdf":
        text = extract_text_from_pdf(file_bytes)
    elif ext in ("docx", "doc"):
        text = extract_text_from_docx(file_bytes)
    else:
        raise ValueError(f"Unsupported file type: {ext}")

    edu_label, edu_level = extract_education_level(text)

    return {
        "name": extract_name(text),
        "email": extract_email(text),
        "phone": extract_phone(text),
        "skills": extract_skills(text),
        "experience_years": extract_experience_years(text),
        "education_label": edu_label,
        "education_level": edu_level,
        "raw_text": text[:5000],  # Store first 5000 chars
    }