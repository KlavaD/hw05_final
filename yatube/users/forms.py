from django import forms
from django.contrib.auth.forms import UserCreationForm

from users.models import User


class CreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = (
            'first_name', 'last_name', 'username', 'email', 'image',
            'birth_date')


class ChangeForm(forms.ModelForm):
    class Meta:
        model = User
        fields = (
            'first_name', 'last_name', 'username', 'email', 'image',
            'birth_date')
