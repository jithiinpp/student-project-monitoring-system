from django import forms
from .models import ProjectProposal


class ProjectProposalForm(forms.ModelForm):

    class Meta:
        model = ProjectProposal

        fields = [
            "title",
            "domain",
            "technologies",
            "abstract",
            "description",
            "proposal_document",
        ]

        widgets = {
            "title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter project title",
            }),

            "domain": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Example: Artificial Intelligence",
            }),

            "technologies": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Example: Python, Django, PostgreSQL",
            }),

            "abstract": forms.Textarea(attrs={
                "class": "form-control",
                "placeholder": "Enter project abstract",
                "rows": 5,
            }),

            "description": forms.Textarea(attrs={
                "class": "form-control",
                "placeholder": "Describe your project",
                "rows": 8,
            }),

            "proposal_document": forms.ClearableFileInput(attrs={
                "class": "form-control",
                "accept": "application/pdf",
            }),
        }