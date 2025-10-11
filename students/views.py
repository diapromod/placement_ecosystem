from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def student_profile(request):
    student = request.user.student_profile
    return render(request, "students/profile.html", {
        "student": student,
    })