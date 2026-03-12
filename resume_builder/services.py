import os
from google import genai
from google.genai import types
from django.conf import settings

# Configure API key. In a real app, you would define GEMINI_API_KEY in settings.py (via .env)
api_key = getattr(settings, 'GEMINI_API_KEY', os.environ.get("GEMINI_API_KEY", "YOUR_API_KEY"))

def generate_tailored_resume_content(student_profile, master_resume_text, job, jd_text):
    """
    Uses Gemini API to extract points from the master resume, rephrase them,
    and output a structured JSON for a highly relevant resume tailored to the JD.
    """
    if not api_key or api_key == "YOUR_API_KEY":
        # Mocking output so the system doesn't break if API key isn't provided right now
        return '''{
            "objective": "A dedicated student from ''' + student_profile.department + ''' aiming to leverage past experience for the ''' + (job.title if job else 'target') + ''' role.",
            "skills": ["Python", "Django", "Machine Learning", "Communication"],
            "experience": [
                {
                    "title": "Software Engineering Intern",
                    "company": "Tech Corp",
                    "points": ["Developed web applications using Django.", "Optimized backend queries."]
                }
            ],
            "projects": [
                {
                    "name": "Placement Ecosystem",
                    "description": "Built a comprehensive platform for university placements using Django."
                }
            ]
        }'''
    
    # Initialize the new SDK client
    client = genai.Client(api_key=api_key)
    
    prompt = f"""
    You are an expert technical resume writer. I am providing you with a student's profile information, their raw master resume, and the target job description they are applying for.
    Your task is to analyze the student's master resume, extract their experiences, projects, and skills, and then REWRITE and PRIORITIZE them so they highly align with the target job description. The goal is to optimize ATS matching while remaining truthful to their actual experience.

    Student Details (Include these inherently):
    - Department: {student_profile.department}
    - CGPA: {student_profile.cgpa}
    
    Master Resume Content:
    {master_resume_text}
    
    Target Job Description:
    {jd_text}
    """
    
    if job:
        prompt += f"Target Job Role: {job.title} at {job.company_name}\n"

    prompt += """
    Based on the above, please return ONLY a valid JSON object with exactly this schema, using no markdown code blocks outside of the JSON payload. Ensure it can be directly parsed via json.loads:
    {
        "objective": "A powerful 2-3 sentence tailored professional summary highlighting matching skills and intent.",
        "skills": ["Skill 1", "Skill 2"],
        "education": [
            {
                "degree": "Degree Name",
                "institution": "University/School",
                "duration": "Duration (if found)",
                "details": "Major/Specialization/Achievements in education"
            }
        ],
        "experience": [
            {
                "title": "Role Title",
                "company": "Company Name",
                "duration": "Time Period (if found)",
                "points": ["Action-oriented bullet point 1", "Action-oriented bullet point 2"]
            }
        ],
        "projects": [
            {
                "name": "Project Name",
                "duration": "Time Period (if found)",
                "points": ["Bullet 1", "Bullet 2"]
            }
        ],
        "certifications": ["Certification name 1", "Certification name 2"],
        "achievements": ["Achievement/Award 1", "Achievement/Award 2"]
    }
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-flash-latest',
            contents=prompt,
        )
        
        text = response.text.strip()
        # remove possible markdown formatting
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
            
        return text.strip()
    except Exception as e:
        # Fallback if the requested model or API call fails
        print(f"Gemini API Error: {e}")
        raise e
