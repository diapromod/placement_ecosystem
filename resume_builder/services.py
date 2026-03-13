import os
from google import genai
from google.genai import types
from django.conf import settings

# Configure API key
api_key = getattr(settings, 'GEMINI_API_KEY', os.environ.get("GEMINI_API_KEY", "YOUR_API_KEY"))
demo_mode = getattr(settings, 'GEMINI_DEMO_MODE', False)

def generate_tailored_resume_content(student_profile, master_resume_text, job, jd_text):
    """
    Uses Gemini API to extract points from the master resume, rephrase them,
    and output a structured JSON for a highly relevant resume tailored to the JD.
    """
    # High-quality mock data for Demo Mode fail-safe
    mock_json = f'''{{
        "objective": "Highly motivated {student_profile.department} student with a CGPA of {student_profile.cgpa}, seeking to leverage strong technical foundations and project experience for the {(job.title if job else 'target')} role.",
        "skills": ["Python", "Django", "REST APIs", "SQL", "Git", "Machine Learning"],
        "education": [
            {{
                "degree": "Bachelor of Technology",
                "institution": "University of Engineering",
                "duration": "2021 - 2025",
                "details": "Major in {student_profile.department}. Consistent academic performer."
            }}
        ],
        "experience": [
            {{
                "title": "Software Intern",
                "company": "Innovation Labs",
                "duration": "Summer 2024",
                "points": [
                    "Developed and maintained web modules using Django and PostgreSQL.",
                    "Collaborated with cross-functional teams to implement responsive UI components.",
                    "Optimized database queries, reducing load times by 20%."
                ]
            }}
        ],
        "projects": [
            {{
                "name": "Placement Ecosystem",
                "duration": "2024",
                "points": [
                    "Designed a comprehensive placement management system handle student registrations and job matching.",
                    "Integrated Google Gemini API for automated resume tailoring and mock interviews.",
                    "Implemented secure authentication and role-based access control."
                ]
            }}
        ],
        "certifications": ["Google Professional Data Engineer", "AWS Certified Cloud Practitioner"],
        "achievements": ["First Place in Hackathon 2024", "Academic Merit Scholarship Recipient"]
    }}'''

    if not api_key or api_key == "YOUR_API_KEY":
        return mock_json
    
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
    Based on the above, please return ONLY a valid JSON object matching this exact schema:
    {
        "objective": "A 2-3 sentence professional summary tailored to the JD",
        "skills": ["Skill 1", "Skill 2"],
        "education": [
            {
                "degree": "Full Degree Name",
                "institution": "Full Institution Name",
                "duration": "Year range",
                "details": "Key academic highlights"
            }
        ],
        "experience": [
            {
                "title": "Job Title",
                "company": "Company Name",
                "duration": "Duration",
                "points": ["Achievement 1", "Achievement 2"]
            }
        ],
        "projects": [
            {
                "name": "Project Name",
                "duration": "Year/Period",
                "points": ["Highlight 1", "Highlight 2"]
            }
        ],
        "certifications": ["Certification Name 1", "Certification Name 2"],
        "achievements": ["Achievement Name 1", "Achievement Name 2"]
    }
    
    IMPORTANT: 
    - **NO INTERNAL SLUGS**: DO NOT use category names or slugs like 'languages', 'frameworks_libraries', 'databases', 'tools_version_control', or 'web_technologies' as skill names. These are internal database labels and must NOT appear on the resume. Instead, list specific skills like 'Python', 'Django', 'PostgreSQL', 'Git', etc.
    - **HUMAN READABLE**: All text must be natural, professional, and human-readable. Do not return raw code or technical internal identifiers.
    - **FLAT ARRAYS**: Fields like 'certifications', 'achievements', 'skills', and 'points' MUST be flat arrays of STRINGS. Do not nest objects or dictionaries inside them.
    - **NO EMPTY BLOCKS**: If a section (like Projects or Experience) has no relevant content from the master resume, return an empty array `[]` for that field. Do not include boilerplate like "No experience found".
    - Do not include any text, markings, or markdown outside the JSON block.
    """
    
    # Fallback chain for Demo Resiliency
    models_to_try = [
        'gemini-2.5-flash',
        'gemini-2.0-flash', 
        'gemini-1.5-flash', 
        'gemini-1.5-flash-8b', 
        'gemini-1.5-pro',
        'gemini-flash-latest'
    ]
    
    last_error = None
    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
            )
            text = response.text.strip()
            # remove possible markdown formatting
            if text.startswith("```json"):
                text = text[7:]
            elif text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
                
            return text.strip()
        except Exception as e:
            last_error = e
            error_str = str(e).lower()
            # If it's a quota issue or server error, try next model
            if "429" in error_str or "quota" in error_str or "500" in error_str:
                print(f"Fallback: Model {model_name} failed, trying next...")
                continue
            else:
                # If it's a different error, stop and handle
                break

    # If all models fail and we are in demo mode, return the mock data
    if demo_mode:
        print("DEMO MODE: All AI models failed/quota reached. Returning high-quality mock data.")
        return mock_json
    
    # Otherwise raise the last error
    raise last_error
