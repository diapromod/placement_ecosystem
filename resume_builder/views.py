from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import GeneratedResume
from matcher.models import Resume, JobDescription
from jobs.models import Job
from .services import generate_tailored_resume_content
import json

@login_required
def index(request):
    generated = GeneratedResume.objects.filter(student=request.user).order_by('-created_at')
    return render(request, 'resume_builder/index.html', {'resumes': generated})

@login_required
def generate_resume(request, resume_id, jd_id):
    resume = get_object_or_404(Resume, id=resume_id)
    job_desc = get_object_or_404(JobDescription, id=jd_id)
    
    # Attempt to find the job associated with this JD
    # In placement ecosystem, Job has a jd_file field. We can try to match the filename.
    job = None
    if job_desc.file:
        job = Job.objects.filter(jd_file__icontains=job_desc.file.name.split('/')[-1]).first()
    
    # Generate content using Gemini
    try:
        # Pass the extracted text from the models
        content_json_str = generate_tailored_resume_content(
            student_profile=request.user.student_profile,
            master_resume_text=resume.raw_text,
            job=job,
            jd_text=job_desc.raw_text
        )
        content_raw = json.loads(content_json_str)
        content = clean_resume_content(content_raw)
        error = None
    except Exception as e:
        content = None
        error = str(e)
        content_json_str = ""
    
    if not error:
        # Save history
        GeneratedResume.objects.create(
            student=request.user,
            target_job_description=job_desc,
            source_resume=resume,
            generated_content=content_json_str
        )
    
    return render(request, 'resume_builder/resume_template.html', {
        'content': content,
        'student': request.user.student_profile,
        'job': job,
        'error': error,
        # Get the latest generated resume id to pass to the download button
        'generated_id': GeneratedResume.objects.filter(student=request.user).order_by('-created_at').first().id if not error else None
    })

from django.http import HttpResponse, Http404
from django.template.loader import render_to_string
from .utils import escape_latex, compile_latex_to_pdf

def clean_resume_content(content):
    """
    Cleans and flattens AI-generated content to ensure it's human-readable
    and safe for both HTML and LaTeX rendering.
    """
    def flatten(val):
        if isinstance(val, dict):
            # Try to find common text fields
            name = val.get('name') or val.get('title') or val.get('value')
            if name: return str(name)
            # Fallback to joining items
            return ", ".join(f"{str(v)}" for v in val.values() if v)
        return str(val)

    cleaned = {}
    
    # Simple text fields
    if 'objective' in content:
        cleaned['objective'] = flatten(content['objective'])
    
    # Simple lists
    for field in ['skills', 'certifications', 'achievements']:
        if field in content:
            raw_list = content.get(field, [])
            if isinstance(raw_list, list):
                cleaned[field] = [flatten(item) for item in raw_list if item]
            else:
                cleaned[field] = [flatten(raw_list)]

    # Nested structures
    cleaned['education'] = []
    for edu in content.get('education', []):
        cleaned['education'].append({
            'degree': flatten(edu.get('degree', '')),
            'institution': flatten(edu.get('institution', '')),
            'duration': flatten(edu.get('duration', '')),
            'details': flatten(edu.get('details', ''))
        })

    cleaned['experience'] = []
    for exp in content.get('experience', []):
        cleaned['experience'].append({
            'title': flatten(exp.get('title', '')),
            'company': flatten(exp.get('company', '')),
            'duration': flatten(exp.get('duration', '')),
            'points': [flatten(p) for p in exp.get('points', []) if p]
        })
        
    cleaned['projects'] = []
    for proj in content.get('projects', []):
        cleaned['projects'].append({
            'name': flatten(proj.get('name', '')),
            'duration': flatten(proj.get('duration', '')),
            'points': [flatten(p) for p in proj.get('points', []) if p]
        })
        
    return cleaned

@login_required
def download_pdf(request, generated_id):
    """
    Takes a GeneratedResume JSON, escapes its content to LaTeX format,
    applies the variables to the .tex template, and compiles it via the API.
    """
    gen_resume = get_object_or_404(GeneratedResume, id=generated_id, student=request.user)
    
    try:
        raw_content = json.loads(gen_resume.generated_content)
        student_profile = request.user.student_profile
        
        # 1. Clean data (flatten dicts, etc)
        content = clean_resume_content(raw_content)

        # 2. Escape for LaTeX
        escaped_content = {
            'objective': escape_latex(content.get('objective', '')),
            'skills': [escape_latex(s) for s in content.get('skills', [])],
            'certifications': [escape_latex(c) for c in content.get('certifications', [])],
            'achievements': [escape_latex(a) for a in content.get('achievements', [])],
            'education': [],
            'experience': [],
            'projects': []
        }
        
        for edu in content['education']:
            escaped_content['education'].append({k: escape_latex(v) for k, v in edu.items()})

        for exp in content['experience']:
            cleaned_exp = {k: escape_latex(v) if k != 'points' else [escape_latex(p) for p in v] 
                          for k, v in exp.items()}
            escaped_content['experience'].append(cleaned_exp)

        for proj in content['projects']:
            cleaned_proj = {k: escape_latex(v) if k != 'points' else [escape_latex(p) for p in v] 
                           for k, v in proj.items()}
            escaped_content['projects'].append(cleaned_proj)
            
        # Also escape student facts
        context = {
            'content': escaped_content,
            'student': {
                'first_name': escape_latex(student_profile.first_name),
                'last_name': escape_latex(student_profile.last_name),
                'email': escape_latex(student_profile.email),
                'contact_no': escape_latex(student_profile.contact_no),
                'university_roll_no': escape_latex(student_profile.university_roll_no),
                'department': escape_latex(student_profile.department),
                'cgpa': student_profile.cgpa,
                'year_of_passout': student_profile.year_of_passout,
            }
        }
        
        # Render the template into raw LaTeX string
        tex_string = render_to_string('resume_builder/resume_template.tex', context)
        
        # Compile it to PDF
        pdf_bytes = compile_latex_to_pdf(tex_string)
        
        # Return as PDF file
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        filename = f"{student_profile.first_name}_{student_profile.last_name}_Resume.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
        
    except Exception as e:
        return HttpResponse(f"Failed to generate PDF: {str(e)}", status=500)

@login_required
def view_resume(request, generated_id):
    """
    Displays a previously generated resume without re-triggering the AI.
    Handles data cleaning and flattening for consistent rendering.
    """
    gen_resume = get_object_or_404(GeneratedResume, id=generated_id, student=request.user)
    
    try:
        raw_content = json.loads(gen_resume.generated_content)
        content = clean_resume_content(raw_content)
    except Exception as e:
        return redirect('resume_builder:index') # Fallback if data is corrupted
        
    return render(request, 'resume_builder/resume_template.html', {
        'content': content,
        'student': request.user.student_profile,
        'generated_id': gen_resume.id
    })

@login_required
def delete_resume(request, resume_id):
    """
    Deletes a specific generated resume.
    """
    resume = get_object_or_404(GeneratedResume, id=resume_id, student=request.user)
    if request.method == "POST":
        resume.delete()
        return redirect('resume_builder:index')
    return render(request, 'resume_builder/confirm_delete.html', {'resume': resume})
