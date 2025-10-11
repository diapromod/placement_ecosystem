from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponse
from openpyxl import Workbook
from .forms import JobForm
from .models import Job, Application
from users.models import StudentProfile

@login_required
def post_job(request):
    if request.user.role != "coordinator":  # ensure only coordinators can post
        messages.error(request, "You are not authorized to post jobs.")
        return redirect("student_dashboard")

    if request.method == "POST":
        form = JobForm(request.POST, request.FILES)
        if form.is_valid():
            job = form.save(commit=False)
            job.created_by = request.user
            job.save()
            messages.success(request, "Job posted successfully!")
            return redirect("manage_jobs")  # Coordinator’s job list
    else:
        form = JobForm()

    return render(request, "jobs/post_job.html", {"form": form})

@login_required
def manage_jobs(request):
    jobs = Job.objects.filter(created_by=request.user).order_by('-created_at')
    return render(request, 'jobs/manage_jobs.html', {'jobs': jobs})

@login_required
def close_applications(request, job_id):
    job = get_object_or_404(Job, id=job_id, created_by=request.user)
    job.status = 'progress'
    job.save()
    messages.success(request, f"Applications for {job.title} are now closed and marked 'In Progress'.")
    return redirect('manage_jobs')

@login_required
def mark_completed(request, job_id):
    job = get_object_or_404(Job, id=job_id, created_by=request.user)
    job.status = 'closed'
    job.save()
    messages.success(request, f"{job.title} marked as Completed.")
    return redirect('manage_jobs')

@login_required
def edit_job(request, job_id):
    job = get_object_or_404(Job, id=job_id) 

    if request.method == 'POST':
        form = JobForm(request.POST, request.FILES, instance=job)
        if form.is_valid():
            form.save()
            return redirect('manage_jobs')
    else:
        form = JobForm(instance=job)

    return render(request, 'jobs/post_job.html', {'form': form, 'edit_mode': True, 'job': job})

@login_required
def job_list(request):
    """List all jobs with eligibility-based apply button."""
    student_profile = get_object_or_404(StudentProfile, user=request.user)
    jobs = Job.objects.filter(status='open', deadline__gte=timezone.now()).order_by('-created_at')

    applied_jobs = Application.objects.filter(student=request.user).values_list('job_id', flat=True)

    job_status = {}
    for job in jobs:
        if job.id in applied_jobs:
            job_status[job.id] = "applied"
        elif student_profile.cgpa < job.min_cgpa:
            job_status[job.id] = "low_cgpa"
        elif student_profile.active_backlogs > job.max_backlogs:
            job_status[job.id] = "too_many_backlogs"
        elif not job.history_allowed and student_profile.history_of_backlogs:
            job_status[job.id] = "history_not_allowed"
        elif student_profile.highest_slab_placed and job.slab <= student_profile.highest_slab_placed:
            job_status[job.id] = "already_placed_same_or_higher"
        else:
            job_status[job.id] = "eligible"

    context = {
        "jobs": jobs,
        "job_status": job_status,
    }
    return render(request, "students/job_list.html", context)

@login_required
def job_list(request):
    """List all coordinator-posted jobs and show eligibility status."""
    student_profile = get_object_or_404(StudentProfile, user=request.user)
    jobs = Job.objects.all().order_by('-created_at')
    applied_jobs = Application.objects.filter(student=request.user).values_list('job_id', flat=True)

    job_status = {}
    for job in jobs:
        if job.id in applied_jobs:
            job_status[job.id] = "applied"
        elif student_profile.cgpa < job.min_cgpa:
            job_status[job.id] = "low_cgpa"
        elif student_profile.active_backlogs > job.max_backlogs:
            job_status[job.id] = "too_many_backlogs"
        elif not job.history_allowed and student_profile.history_of_backlogs:
            job_status[job.id] = "history_not_allowed"
        elif student_profile.highest_slab_placed and job.slab <= student_profile.highest_slab_placed:
            job_status[job.id] = "already_placed_same_or_higher"
        else:
            job_status[job.id] = "eligible"

    context = {
        "jobs": jobs,
        "job_status": job_status,
    }
    return render(request, "students/apply_jobs.html", context)


@login_required
def apply_job(request, job_id):
    """Allow eligible students to apply."""
    job = get_object_or_404(Job, id=job_id)
    student_profile = get_object_or_404(StudentProfile, user=request.user)

    # Eligibility checks
    if student_profile.cgpa < job.min_cgpa:
        messages.error(request, "Not eligible: CGPA below required minimum.")
    elif student_profile.active_backlogs > job.max_backlogs:
        messages.error(request, "Not eligible: Too many backlogs.")
    elif not job.history_allowed and student_profile.history_of_backlogs:
        messages.error(request, "Not eligible: History of backlogs not allowed.")
    elif student_profile.highest_slab_placed and job.slab <= student_profile.highest_slab_placed:
        messages.error(request, "Not eligible: Already placed in same or higher slab.")
    else:
        Application.objects.get_or_create(student=request.user, job=job)
        messages.success(request, f"Applied successfully for {job.title}!")
    return redirect("job_list")


@login_required
def track_applications(request):
    applications = Application.objects.filter(student=request.user).select_related('job')
    return render(request, 'students/track_applications.html', {'applications': applications})

@login_required
def export_applicants_excel(request, job_id):
    job = Job.objects.get(id=job_id)
    applicants = Application.objects.filter(job=job)

    # Create workbook
    wb = Workbook()
    ws = wb.active
    ws.title = f"{job.title} Applicants"

    # Header row
    ws.append([
        "First Name",
        "Last Name",
        "University Roll No", 
        "Email",
        "Contact No.",
        "Department",
        "CGPA",
        "No. of Active Backlogs",
        "History of Backlogs",
    ])

    for app in applicants:
        user = app.student 
        profile = user.student_profile
        ws.append([
            # Data from StudentProfile
            profile.first_name,
            profile.last_name,
            profile.university_roll_no,
            profile.email,
            profile.contact_no,
            profile.department,
            profile.cgpa,
            profile.active_backlogs,
            'Yes' if profile.history_of_backlogs else 'No'
        ])

    # Prepare response
    response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    filename = f"{job.title}_applicants.xlsx"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    wb.save(response)
    return response
