from django.contrib import admin
from .models import Resume, JobDescription

@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "email", "uploaded_at")
    readonly_fields = ("raw_text",)

@admin.register(JobDescription)
class JDAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "uploaded_at")
    readonly_fields = ("raw_text",)
