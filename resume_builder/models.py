from django.db import models
from django.conf import settings
from matcher.models import JobDescription, Resume
from matcher.models import Resume

class GeneratedResume(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="generated_resumes")
    target_job_description = models.ForeignKey(JobDescription, on_delete=models.SET_NULL, null=True, blank=True)
    source_resume = models.ForeignKey(Resume, on_delete=models.SET_NULL, null=True, blank=True)
    generated_content = models.TextField(help_text="The tailored HTML/JSON content for this resume")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Generated Resume for {self.student.username} - {self.created_at.date()}"
