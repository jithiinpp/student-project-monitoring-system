from django import forms
from .models import ProjectProposal, ProjectProgress


# =========================================================
# PROJECT PROPOSAL FORM
# =========================================================

class ProjectProposalForm(forms.ModelForm):

    class Meta:
        model = ProjectProposal

        fields = [
            "title",
            "abstract",
            "domain",
            "technologies",
            "description",
            "proposal_document",
        ]

        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter project title",
                }
            ),

            "abstract": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                    "placeholder": "Enter project abstract",
                }
            ),

            "domain": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter project domain",
                }
            ),

            "technologies": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Python, Django, HTML, CSS, JavaScript",
                }
            ),

            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 6,
                    "placeholder": "Enter project description",
                }
            ),

            "proposal_document": forms.ClearableFileInput(
                attrs={
                    "class": "form-control",
                    "accept": ".pdf,.doc,.docx",
                }
            ),
        }


# =========================================================
# PROJECT PROGRESS FORM
# =========================================================

class ProjectProgressForm(forms.ModelForm):

    class Meta:
        model = ProjectProgress

        fields = [
            "title",
            "description",
            "document",
        ]

        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter report title",
                }
            ),

            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 7,
                    "placeholder": "Describe your project progress...",
                }
            ),

            "document": forms.ClearableFileInput(
                attrs={
                    "class": "form-control",
                    "accept": ".pdf,.doc,.docx",
                }
            ),
        }