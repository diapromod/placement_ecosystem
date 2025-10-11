from django.urls import path
from . import views

urlpatterns = [
    path('profile/', views.student_profile, name='student_profile'),
]
