from django import forms
from .models import Job

class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = [
            "title", "company_name", "location", "ctc", "deadline",
            "min_cgpa", "max_backlogs", "history_allowed", "jd_file"
        ]
        widgets = {
            "deadline": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }
