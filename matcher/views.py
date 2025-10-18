from django.shortcuts import render, redirect
from django.urls import reverse
from django.conf import settings
from django.core.files.storage import default_storage
from .forms import ResumeUploadForm
from .models import Resume, JobDescription
from . import utils

def home(request):
    """
    Home view: upload resume and optional JD, parse and show results.
    """
    context = {"form": None, "result": None, "error": None}
    if request.method == "POST":
        form = ResumeUploadForm(request.POST, request.FILES)
        context["form"] = form
        if form.is_valid():
            resume_file = request.FILES.get("resume")
            jd_file = request.FILES.get("jd")

            # Save resume model (optional persistent)
            r = Resume.objects.create(file=resume_file)
            # extract text
            try:
                resume_text = utils.extract_text_from_file(resume_file)
            except Exception as e:
                resume_text = ""
            r.raw_text = resume_text

            # extract simple features
            r.name = utils.extract_name(resume_text) or ""
            r.email = utils.extract_email(resume_text) or ""
            r.phone = utils.extract_phone(resume_text) or ""
            r.skills = utils.extract_skills_from_text(resume_text)
            r.save()

            jd_obj = None
            jd_text = ""
            jd_skills = []
            if jd_file:
                jd_obj = JobDescription.objects.create(file=jd_file)
                try:
                    jd_text = utils.extract_text_from_file(jd_file)
                except Exception:
                    jd_text = ""
                jd_obj.raw_text = jd_text
                jd_obj.required_skills = utils.parse_jd_for_skills(jd_text)
                jd_obj.save()
                jd_skills = jd_obj.required_skills or []

            # Compute matching: both simple jaccard & heuristic on skills
            res_skills = r.skills or []
            jacc = utils.jaccard_score(res_skills, jd_skills) if jd_skills else None
            heur = utils.heuristic_weighted_score(res_skills, jd_skills) if jd_skills else None

            # optional SBERT semantic score if installed
            sbert_score = None
            if jd_text and utils.SBERT_AVAILABLE:
                try:
                    sbert_score = utils.sbert_similarity_score(resume_text, jd_text)
                except Exception:
                    sbert_score = None

            # ✅ Convert fractional scores (0–1) → percentages (0–100)
            if jacc is not None:
                jacc = round(jacc * 100, 2)
            if heur is not None:
                heur = round(heur * 100, 2)
            if sbert_score is not None:
                sbert_score = round(sbert_score * 100, 2)

            # Now render context
            context["result"] = {
                "name": r.name,
                "email": r.email,
                "phone": r.phone,
                "skills": res_skills,
                "jd_skills": jd_skills,
                "jaccard": jacc,
                "heuristic_score": heur,
                "sbert_score": sbert_score,
                "resume_id": r.id,
                "jd_id": jd_obj.id if jd_obj else None,
            }

            return render(request, "matcher/result.html", context)
        else:
            context["error"] = "Form is invalid."
    else:
        context["form"] = ResumeUploadForm()
    return render(request, "matcher/home.html", context)
