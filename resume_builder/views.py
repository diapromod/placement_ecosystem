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
        content = json.loads(content_json_str)
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

@login_required
def download_pdf(request, generated_id):
    """
    Takes a GeneratedResume JSON, escapes its content to LaTeX format,
    applies the variables to the .tex template, and compiles it via the API.
    """
    gen_resume = get_object_or_404(GeneratedResume, id=generated_id, student=request.user)
    
    try:
        content = json.loads(gen_resume.generated_content)
        student_profile = request.user.student_profile
        
        # We must escape all strings in the content dict before sending to LaTeX
        escaped_content = {}
        if 'objective' in content: escaped_content['objective'] = escape_latex(content['objective'])
        if 'skills' in content: escaped_content['skills'] = [escape_latex(s) for s in content['skills']]
        
        escaped_content['education'] = []
        for edu in content.get('education', []):
            escaped_content['education'].append({
                'degree': escape_latex(edu.get('degree', '')),
                'institution': escape_latex(edu.get('institution', '')),
                'duration': escape_latex(edu.get('duration', '')),
                'details': escape_latex(edu.get('details', ''))
            })

        escaped_content['experience'] = []
        for exp in content.get('experience', []):
            escaped_content['experience'].append({
                'title': escape_latex(exp.get('title', '')),
                'company': escape_latex(exp.get('company', '')),
                'duration': escape_latex(exp.get('duration', '')),
                'points': [escape_latex(p) for p in exp.get('points', [])]
            })
            
        escaped_content['projects'] = []
        for proj in content.get('projects', []):
            escaped_content['projects'].append({
                'name': escape_latex(proj.get('name', '')),
                'duration': escape_latex(proj.get('duration', '')),
                'points': [escape_latex(p) for p in proj.get('points', [])]
            })

        escaped_content['certifications'] = [escape_latex(c) for c in content.get('certifications', [])]
        escaped_content['achievements'] = [escape_latex(a) for a in content.get('achievements', [])]
            
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
def delete_resume(request, resume_id):
    """
    Deletes a specific generated resume.
    """
    resume = get_object_or_404(GeneratedResume, id=resume_id, student=request.user)
    if request.method == "POST":
        resume.delete()
        return redirect('resume_builder:index')
    return render(request, 'resume_builder/confirm_delete.html', {'resume': resume})
