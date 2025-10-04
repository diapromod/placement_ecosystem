from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def student_dashboard(request):
    student = request.user.student_profile
    notifications = [
        {"title": "Google Recruitment Drive", "category": "Job", "description": "Apply before Oct 10"},
        {"title": "Resume Workshop", "category": "Event", "description": "Join us on Oct 15"},
    ]
    return render(request, "students/student_dashboard.html", {
        "student": student,
        "notifications": notifications
    })