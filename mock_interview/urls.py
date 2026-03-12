from django.urls import path
from . import views

app_name = 'mock_interview'

urlpatterns = [
    path('', views.index, name='index'),
    path('start/', views.start_session, name='start_session'),
    path('session/<int:session_id>/', views.chat_view, name='chat_view'),
    path('session/<int:session_id>/delete/', views.delete_session, name='delete_session'),
    path('feedback/<int:session_id>/', views.feedback_view, name='feedback_view'),
]
