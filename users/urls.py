# users/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("student/signup/", views.student_register, name="student_signup"),
    path("student/login/", views.student_login, name="student_login"),
    path("coordinator/login/", views.coordinator_login, name="coordinator_login"),
]
