from django.urls import path
from . import views

urlpatterns = [
    path('profile/', views.student_profile, name='student_profile'),
    path('ai-tools/', views.ai_tools, name='ai_tools'),
]
