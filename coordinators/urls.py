from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.coordinator_dashboard, name='coordinator_dashboard'),
]
