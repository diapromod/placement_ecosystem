from django.urls import path
from . import views

app_name = 'resume_builder'

urlpatterns = [
    path('', views.index, name='index'),
    path('generate/<int:resume_id>/<int:jd_id>/', views.generate_resume, name='generate_resume'),
    path('download-pdf/<int:generated_id>/', views.download_pdf, name='download_pdf'),
    path('delete/<int:resume_id>/', views.delete_resume, name='delete_resume'),
]
