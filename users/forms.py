from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, StudentProfile


class StudentRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = CustomUser
        fields = ["username", "email", "password1", "password2"]

    # Save both CustomUser and StudentProfile
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.is_active = True   # student accounts are active by default
        if commit:
            user.save()
            # Create linked student profile
            StudentProfile.objects.create(
                user=user,
                first_name=self.cleaned_data.get("first_name", ""),
                last_name=self.cleaned_data.get("last_name", ""),
                contact_no=self.cleaned_data.get("contact_no", ""),
                university_roll_no=self.cleaned_data.get("university_roll_no", ""),
                cgpa=self.cleaned_data.get("cgpa", 0.0),
                department=self.cleaned_data.get("department", ""),
                year_of_passout=self.cleaned_data.get("year_of_passout", None),
                active_backlogs=self.cleaned_data.get("active_backlogs", 0),
                history_of_backlogs=self.cleaned_data.get("history_of_backlogs", False),
            )
        return user


# Extra fields for StudentProfile
class StudentExtraForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        exclude = ["user"]
