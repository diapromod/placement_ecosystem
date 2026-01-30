from matcher.models import Resume, JobDescription
from .adapters import extract_missing_skills
from .course_apis import fetch_courses
from .ranking import score_courses

def pipeline(resume_id, jd_id):
    """
    Orchestrate the learning path recommendation process.
    Returns a dict with 'job_ready' (bool) and 'courses' (list of top 3 courses).
    """
    try:
        resume = Resume.objects.get(id=resume_id)
        jd = JobDescription.objects.get(id=jd_id)
    except (Resume.DoesNotExist, JobDescription.DoesNotExist):
        return {'job_ready': False, 'courses': [], 'error': 'Invalid resume or job description ID'}

    resume_skills = resume.skills or []
    jd_skills = jd.required_skills or []
    missing_skills = extract_missing_skills(resume_skills, jd_skills)

    if not missing_skills:
        return {'job_ready': True, 'courses': [], 'missing_skills': []}

    # Assign skill priorities (higher for earlier in list, assuming order matters)
    skill_priorities = {skill: len(missing_skills) - i for i, skill in enumerate(missing_skills)}

    all_courses = []
    for skill in missing_skills:
        skill_courses = fetch_courses(skill)
        for course in skill_courses:
            course['skill'] = skill  # Ensure skill is set
        all_courses.extend(skill_courses)

    scored_courses = score_courses(all_courses, skill_priorities)
    top_courses = scored_courses[:3]

    return {'job_ready': False, 'courses': top_courses, 'missing_skills': missing_skills}