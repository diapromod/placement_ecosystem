# users/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .forms import StudentRegistrationForm
from .models import CustomUser

# Student Signup
def student_register(request):
    if request.method == "POST":
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Registration successful! Please log in.")
            return redirect("student_login")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = StudentRegistrationForm()
    return render(request, "users/student_register.html", {"form": form})


# Student Login
def student_login(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None and user.role == "student":
            login(request, user)
            return redirect("student_profile")
        else:
            messages.error(request, "Invalid credentials or not a student.")
    return render(request, "users/student_login.html")

# Coordinator Login
def coordinator_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if user is not None and user.role == "coordinator":
            login(request, user)
            return redirect("manage_jobs")  # will create this
        else:
            messages.error(request, "Invalid credentials or not a coordinator.")
    return render(request, "users/coordinator_login.html")

#Logout for both roles
def user_logout(request):
    role = None
    if request.user.is_authenticated:
        role = request.user.role
        logout(request)

    # Redirect to the correct login page based on role
    if role == "student":
        return redirect("student_login")
    elif role == "coordinator":
        return redirect("coordinator_login")
    else:
        return redirect("student_login")  # default fallback
