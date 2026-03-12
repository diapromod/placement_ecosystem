from django.db import models
from django.conf import settings
from matcher.models import JobDescription

class InterviewSession(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="interview_sessions")
    target_jd = models.ForeignKey(JobDescription, on_delete=models.CASCADE)
    overall_score = models.IntegerField(null=True, blank=True)
    feedback_summary = models.TextField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Interview: {self.student.username} - {self.target_jd.title} ({self.created_at.date()})"

class InterviewMessage(models.Model):
    session = models.ForeignKey(InterviewSession, on_delete=models.CASCADE, related_name="messages")
    sender = models.CharField(max_length=10, choices=[('ai', 'AI'), ('user', 'User')])
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.sender.upper()}: {self.content[:50]}..."
