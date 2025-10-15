from django import forms
from .models import Resume, JobDescription

class ResumeUploadForm(forms.Form):
    resume = forms.FileField(required=True)
    jd = forms.FileField(required=False)  # optional JD upload for demo/matching

    # if you prefer model forms:
    # class Meta:
    #    model = Resume
    #    fields = ['file']
