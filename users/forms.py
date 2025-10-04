from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, StudentProfile


class StudentRegistrationForm(UserCreationForm):
    # Extra StudentProfile fields
    first_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={"placeholder": "First Name"})
    )
    last_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={"placeholder": "Last Name"})
    )
    contact_no = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Contact Number"})
    )
    university_roll_no = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={"placeholder": "University Roll Number"})
    )
    cgpa = forms.DecimalField(
        max_digits=4,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={"placeholder": "CGPA"})
    )
    department = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={"placeholder": "Department"})
    )
    year_of_passout = forms.IntegerField(
        widget=forms.NumberInput(attrs={"placeholder": "Year of Passout"})
    )
    active_backlogs = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={"placeholder": "Active Backlogs"})
    )
    history_of_backlogs = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput()
    )

    class Meta:
        model = CustomUser
        fields = ["username", "email", "password1", "password2"]  # ✅ only CustomUser fields
        widgets = {
            "username": forms.TextInput(attrs={"placeholder": "Username"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].widget.attrs.update({"placeholder": "Enter your email"})
        self.fields["password1"].widget.attrs.update({"placeholder": "Password"})
        self.fields["password2"].widget.attrs.update({"placeholder": "Confirm Password"})

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = "student"
        if commit:
            user.save()
            StudentProfile.objects.create(
                user=user,
                first_name=self.cleaned_data["first_name"],
                last_name=self.cleaned_data["last_name"],
                contact_no=self.cleaned_data["contact_no"],
                university_roll_no=self.cleaned_data["university_roll_no"],
                cgpa=self.cleaned_data["cgpa"],
                department=self.cleaned_data["department"],
                year_of_passout=self.cleaned_data["year_of_passout"],
                active_backlogs=self.cleaned_data["active_backlogs"],
                history_of_backlogs=self.cleaned_data["history_of_backlogs"],
                email=self.cleaned_data["email"],
            )
        return user
