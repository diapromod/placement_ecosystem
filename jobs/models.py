from django.db import models
from django.conf import settings
from django.utils import timezone

User = settings.AUTH_USER_MODEL

class Job(models.Model):
    SLAB_CHOICES = [
        (1, "Slab 1 (< 6 LPA)"),
        (2, "Slab 2 (6–12 LPA)"),
        (3, "Slab 3 (>= 12 LPA)"),
    ]
    STATUS_CHOICES = [
        ('open', 'Applications Open'),
        ('progress', 'In Progress'),
        ('closed', 'Completed'),
    ]
    title = models.CharField(max_length=255)
    company_name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    ctc = models.DecimalField(max_digits=10, decimal_places=2)  # LPA
    slab = models.IntegerField(choices=SLAB_CHOICES, blank=True, null=True)

    deadline = models.DateTimeField()
    min_cgpa = models.DecimalField(max_digits=4, decimal_places=2)
    max_backlogs = models.IntegerField(default=0)
    history_allowed = models.BooleanField(default=True)

    jd_file = models.FileField(upload_to="job_descriptions/",null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posted_jobs")
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')

    def save(self, *args, **kwargs):
        """Auto-assign slab based on CTC before saving"""
        if self.ctc < 600000:
            self.slab = 1
        elif self.ctc < 1200000:
            self.slab = 2
        else:
            self.slab = 3
        super().save(*args, **kwargs)

    def is_application_open(self):
        from django.utils import timezone
        return self.deadline >= timezone.now().date() and self.status == 'open'

    def __str__(self):
        return f"{self.title} at {self.company_name}"


class Application(models.Model):
    STATUS_CHOICES = [
        ("Applied", "Applied"),
        ("Shortlisted", "Shortlisted"),
        ("Rejected", "Rejected"),
        ("Selected", "Selected"),
    ]

    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="applications")
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="applications")
    applied_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Applied")

    class Meta:
        unique_together = ("student", "job")  # Prevent multiple applications

    def __str__(self):
        return f"{self.student} → {self.job}"
