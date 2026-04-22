COMMON_SKILLS = list(set([
    "python", "java", "machine learning", "deep learning",
    "sql", "excel", "tensorflow", "pytorch", "fastapi",
    "docker", "kubernetes", "aws", "azure", "gcp", "nlp",
    "computer vision", "data analysis", "data visualization",
    "git", "linux", "bash",

    # Soft skills
    "communication", "teamwork", "problem solving", "leadership",
    "project management", "time management", "adaptability",
    "critical thinking", "creativity", "collaboration",

    # Business / non-tech
    "sales", "marketing", "finance", "accounting",
    "human resources", "recruitment"
]))

def extract_skills(text):
    text = text.lower()

    found = []
    for skill in COMMON_SKILLS:
        if f" {skill} " in f" {text} ":
            found.append(skill)

    return found