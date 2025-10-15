from django.db import models

class Resume(models.Model):
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file = models.FileField(upload_to="resumes/")
    name = models.CharField(max_length=200, blank=True, null=True)
    email = models.CharField(max_length=200, blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    skills = models.JSONField(blank=True, null=True)  # list
    raw_text = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.name or 'Resume'} - {self.uploaded_at.date()}"


class JobDescription(models.Model):
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file = models.FileField(upload_to="jds/")
    title = models.CharField(max_length=256, blank=True, null=True)
    required_skills = models.JSONField(blank=True, null=True)
    raw_text = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.title or 'JD'} - {self.uploaded_at.date()}"
