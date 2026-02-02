# users/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .forms import StudentRegistrationForm
from .models import CustomUser
from matcher import utils  # Import matcher util for parsing

def process_resume(request):
    """Handle resume upload, parse it, and store data in session."""
    print("DEBUG: process_resume view called")
    if request.method == "POST" and request.FILES.get("resume"):
        resume_file = request.FILES["resume"]
        print(f"DEBUG: File received: {resume_file.name}, size: {resume_file.size}")
        try:
            text = utils.extract_text_from_file(resume_file)
            print(f"DEBUG: Extracted text length: {len(text)}")
            if not text:
                print("DEBUG: No text extracted!")
            
            # Extract all fields
            name = utils.extract_name(text) or ""
            email = utils.extract_email(text) or ""
            phone = utils.extract_phone(text) or ""
            cgpa = utils.extract_cgpa(text)
            department = utils.extract_department(text) or ""
            
            print(f"DEBUG: Extracted - Name: {name}, Email: {email}, Phone: {phone}, CGPA: {cgpa}, Dept: {department}")

            # Split name into first/last
            parts = name.split()
            first_name = parts[0] if parts else ""
            last_name = " ".join(parts[1:]) if len(parts) > 1 else ""

            # Store in session
            request.session["registration_data"] = {
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "contact_no": phone,
                "cgpa": cgpa,
                "department": department,
            }
            print("DEBUG: Session data set:", request.session["registration_data"])
            messages.success(request, "Resume parsed successfully! Please review details.")
        except Exception as e:
            print(f"DEBUG: Exception during parsing: {e}")
            messages.error(request, f"Error parsing resume: {e}")
    else:
        print("DEBUG: No file found in POST request")
            
    return redirect("student_register")

# Student Signup
def student_register(request):
    # Check for pre-filled data from session (don't pop yet, in case validity check fails)
    initial_data = request.session.get("registration_data", None)
    
    if request.method == "POST":
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            # clear session data only after successful save
            if "registration_data" in request.session:
                del request.session["registration_data"]
            messages.success(request, "Registration successful! Please log in.")
            return redirect("student_login")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        # Pre-fill form if data exists
        form = StudentRegistrationForm(initial=initial_data) if initial_data else StudentRegistrationForm()
        # Optionally clear it if you only want it to persist for one render:
        # if "registration_data" in request.session:
        #    del request.session["registration_data"]
        
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
