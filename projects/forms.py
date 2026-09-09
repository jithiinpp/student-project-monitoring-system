from django import forms

from .models import ProjectProposal, ProjectProgress


# ============================================================
# PROJECT PROPOSAL FORM
# ============================================================

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

            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter project title",
                }
            ),

            "domain": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Example: Artificial Intelligence",
                }
            ),

            "technologies": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Example: Python, Django, PostgreSQL",
                }
            ),

            "abstract": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter project abstract",
                    "rows": 5,
                }
            ),

            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Describe your project",
                    "rows": 8,
                }
            ),

            "proposal_document": forms.ClearableFileInput(
                attrs={
                    "class": "form-control",
                    "accept": "application/pdf",
                }
            ),
        }


# ============================================================
# WEEKLY PROJECT PROGRESS FORM
# ============================================================

class ProjectProgressForm(forms.ModelForm):

    class Meta:

        model = ProjectProgress

        fields = [
            "week_number",
            "title",
            "description",
            "document",
        ]

        widgets = {

            "week_number": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Example: 1",
                    "min": 1,
                }
            ),

            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Example: Database Design Completed",
                }
            ),

            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": (
                        "Describe the work completed this week..."
                    ),
                    "rows": 7,
                }
            ),

            "document": forms.ClearableFileInput(
                attrs={
                    "class": "form-control",
                    "accept": ".pdf,.doc,.docx",
                }
            ),
        }

    def clean_week_number(self):

        week_number = self.cleaned_data.get("week_number")

        if week_number is not None and week_number < 1:
            raise forms.ValidationError(
                "Week number must be at least 1."
            )

        return week_number