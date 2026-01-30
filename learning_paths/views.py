from django.shortcuts import render
from .services.pipeline import pipeline

def intro(request):
    return render(request, 'learning_paths/intro.html')

def recommend(request, resume_id, jd_id):
    result = pipeline(resume_id, jd_id)
    return render(request, 'learning_paths/result.html', {'result': result})