from django import forms
from django.core.exceptions import ValidationError

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
            "technologies": "Technologies",
            "description": "Project Description",
            "proposal_document": "Proposal Document",
        }


# =========================================================
# PROJECT PROGRESS FORM
# =========================================================

class ProjectProgressForm(forms.ModelForm):
    week_number = forms.IntegerField(
        required=False,
        min_value=1,
        max_value=3,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "min": 1,
                "max": 3,
                "placeholder": "Enter week number",
            }
        ),
        label="Week Number",
    )

    def __init__(
        self,
        *args,
        require_week_number=False,
        expected_week_number=None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.require_week_number = require_week_number
        self.expected_week_number = expected_week_number
        self.fields["week_number"].required = require_week_number

    class Meta:
        model = ProjectProgress

        fields = [
            "week_number",
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
                    "accept": ".pdf,application/pdf",
                }
            ),
        }

        labels = {
            "week_number": "Week Number",
            "title": "Progress Title",
            "description": "Work Completed",
            "document": "Supporting Document",
        }

    def clean_week_number(self):
        week_number = self.cleaned_data.get("week_number")

        if self.require_week_number and week_number is None:
            raise ValidationError("Enter the week number for this report.")

        if (
            self.expected_week_number is not None
            and week_number != self.expected_week_number
        ):
            raise ValidationError(
                f"This report must be submitted for Week "
                f"{self.expected_week_number}."
            )

        return week_number

    def clean_document(self):
        document = self.cleaned_data.get("document")
        if document and "document" in self.files:
            if not document.name.lower().endswith(".pdf"):
                raise ValidationError("Only PDF documents are allowed.")

            header = document.read(1024)
            document.seek(0)
            if b"%PDF-" not in header:
                raise ValidationError("Upload a valid PDF document.")

        return document