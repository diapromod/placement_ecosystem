from django.urls import path
from . import views

urlpatterns = [
    path("post/", views.post_job, name="post_job"),
    path('manage_jobs/', views.manage_jobs, name='manage_jobs'),
    path('close_applications/<int:job_id>/', views.close_applications, name='close_applications'),
    path('mark_completed/<int:job_id>/', views.mark_completed, name='mark_completed'),
    path("edit/<int:job_id>/", views.edit_job, name="edit_job"),
    path('jobs/', views.job_list, name='job_list'),
    path('jobs/apply/<int:job_id>/', views.apply_job, name='apply_job'),
    path('track/', views.track_applications, name='track_applications'),
    path('export_applicants/<int:job_id>/', views.export_applicants_excel, name='export_applicants_excel'),
]
