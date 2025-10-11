from django.urls import path
from . import views

urlpatterns = [
    path("post/", views.post_job, name="post_job"),
    path('manage_jobs/', views.manage_jobs, name='manage_jobs'),
    path('close_applications/<int:job_id>/', views.close_applications, name='close_applications'),
    path('mark_completed/<int:job_id>/', views.mark_completed, name='mark_completed'),
    path("edit/<int:job_id>/", views.edit_job, name="edit_job"),
]
