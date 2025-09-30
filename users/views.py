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
            user = form.save(commit=False)
            user.role = "student"  # assuming we added a role field in CustomUser
            user.save()
            messages.success(request, "Registration successful! Please log in.")
            return redirect("student_login")
    else:
        form = StudentRegistrationForm()
    return render(request, "users/student_register.html", {"form": form})

# Student Login
def student_login(request):
    if request.method == "POST":
        email = request.POST["email"]
        password = request.POST["password"]
        user = authenticate(request, email=email, password=password)
        if user is not None and user.role == "student":
            login(request, user)
            return redirect("student_dashboard")  # create later
        else:
            messages.error(request, "Invalid credentials or not a student.")
    return render(request, "users/student_login.html")

# Coordinator Login
def coordinator_login(request):
    if request.method == "POST":
        email = request.POST["email"]
        password = request.POST["password"]
        user = authenticate(request, email=email, password=password)
        if user is not None and user.role == "coordinator":
            login(request, user)
            return redirect("coordinator_dashboard")  # create later
        else:
            messages.error(request, "Invalid credentials or not a coordinator.")
    return render(request, "users/coordinator_login.html")
