from django import forms

from .models import ProjectProgress, ProjectProposal


# =========================================================
# PROJECT PROPOSAL FORM
# =========================================================

class ProjectProposalForm(forms.ModelForm):

    class Meta:
        model = ProjectProposal

        fields = [
            "project_type",
            "title",
            "abstract",
            "domain",
            "technologies",
            "description",
            "proposal_document",
        ]

        widgets = {
            "project_type": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),

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

            "technologies": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Example: Python, Django, HTML, CSS, JavaScript",
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

        labels = {
            "project_type": "Project Type",
            "title": "Project Title",
            "abstract": "Abstract",
            "domain": "Project Domain",
            "technologies": "Technologies",
            "description": "Project Description",
            "proposal_document": "Proposal Document",
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
                    "placeholder": "Enter progress title",
                }
            ),

            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                    "placeholder": "Describe the work completed this week",
                }
            ),

            "document": forms.ClearableFileInput(
                attrs={
                    "class": "form-control",
                    "accept": ".pdf,.doc,.docx",
                }
            ),
        }

        labels = {
            "title": "Progress Title",
            "description": "Progress Details",
            "document": "Progress Document",
        }