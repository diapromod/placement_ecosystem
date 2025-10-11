from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('coordinator', 'Coordinator'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    def __str__(self):
        return f"{self.username} ({self.role})"


class StudentProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="student_profile")
    
    # ---- Basic Info ----
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    contact_no = models.CharField(max_length=15)
    university_roll_no = models.CharField(max_length=20, unique=True)
    department = models.CharField(max_length=100)
    year_of_passout = models.IntegerField()

    # ---- Academic Info ----
    cgpa = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    active_backlogs = models.IntegerField(default=0)
    history_of_backlogs = models.BooleanField(default=False)

    # ---- Placement Info ----
    offers_received = models.IntegerField(default=0)
    companies_placed = models.TextField(blank=True, null=True)  # comma-separated list
    highest_slab_placed = models.IntegerField(default=0, choices=[
        (0, "Not Placed"),
        (1, "Slab 1 (<6 LPA)"),
        (2, "Slab 2 (6–12 LPA)"),
        (3, "Slab 3 (>=12 LPA)")
    ])

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.university_roll_no})"


class CoordinatorProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="coordinator_profile")
    
    # Coordinator-specific fields
    contact_no = models.CharField(max_length=15)

    def __str__(self):
        return f"Coordinator: {self.user.username}"
