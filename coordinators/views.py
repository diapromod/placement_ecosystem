from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def coordinator_dashboard(request):
    if request.user.role != "coordinator":
        return redirect("coordinator_login")  # block students
    return render(request, "coordinators/coordinator_dashboard.html")