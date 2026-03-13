from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from users.models import StudentProfile
from jobs.models import Job, Application

@login_required
def coordinator_dashboard(request):
    if request.user.role != "coordinator":
        return redirect("coordinator_login")  # block students
    
    # Fetch summary stats
    stats = {
        'total_students': StudentProfile.objects.count(),
        'total_jobs': Job.objects.count(),
        'total_applications': Application.objects.count(),
        'placed_students': StudentProfile.objects.filter(offers_received__gt=0).count(),
        'recent_jobs': Job.objects.order_by('-created_at')[:5],
        'recent_applications': Application.objects.order_by('-applied_at')[:5]
    }
    
    return render(request, "coordinators/coordinator_dashboard.html", stats)