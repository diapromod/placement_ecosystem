from django.urls import path
from . import views

app_name = 'learning_paths'

urlpatterns = [
    path('intro/', views.intro, name='intro'),
    path('recommend/<int:resume_id>/<int:jd_id>/', views.recommend, name='recommend'),
]