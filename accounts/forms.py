from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import User


class StudentRegistrationForm(UserCreationForm):

    class Meta:
        model = User

        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "phone",
            "roll_number",
            "department",
            "semester",
            "batch",
            "password1",
            "password2",
        ]

        widgets = {
            "username": forms.TextInput(
                attrs={
                    "placeholder": "Enter username"
                }
            ),

            "first_name": forms.TextInput(
                attrs={
                    "placeholder": "Enter first name"
                }
            ),

            "last_name": forms.TextInput(
                attrs={
                    "placeholder": "Enter last name"
                }
            ),

            "email": forms.EmailInput(
                attrs={
                    "placeholder": "Enter email"
                }
            ),

            "phone": forms.TextInput(
                attrs={
                    "placeholder": "Enter phone number"
                }
            ),

            "roll_number": forms.TextInput(
                attrs={
                    "placeholder": "Enter roll number"
                }
            ),

            "department": forms.TextInput(
                attrs={
                    "placeholder": "Enter department"
                }
            ),

            "semester": forms.TextInput(
                attrs={
                    "placeholder": "Enter semester"
                }
            ),

            "batch": forms.TextInput(
                attrs={
                    "placeholder": "Enter batch"
                }
            ),
        }

    def save(self, commit=True):

        user = super().save(commit=False)

        # Public registration is always Student
        user.role = "STUDENT"

        if commit:
            user.save()

        return user

