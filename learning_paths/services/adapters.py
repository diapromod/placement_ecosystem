def extract_missing_skills(resume_skills, jd_required_skills):
    """
    Extract missing skills from resume compared to job description.
    Assumes skills are lists of strings.
    """
    resume_set = set(resume_skills or [])
    jd_set = set(jd_required_skills or [])
    return list(jd_set - resume_set)