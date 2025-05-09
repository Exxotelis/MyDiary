from django import forms
from .models import UserProfile


class ProfileImageForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['profile_image']
