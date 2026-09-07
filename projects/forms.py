from django import forms

from .models import ProjectProposal


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
                    "placeholder": "Enter project title"
                }
            ),

            "abstract": forms.Textarea(
                attrs={
                    "placeholder": "Enter project abstract",
                    "rows": 5
                }
            ),

            "domain": forms.TextInput(
                attrs={
                    "placeholder": "Example: Artificial Intelligence"
                }
            ),

            "technologies": forms.TextInput(
                attrs={
                    "placeholder": "Example: Python, Django, HTML, CSS"
                }
            ),

            "description": forms.Textarea(
                attrs={
                    "placeholder": "Describe your project",
                    "rows": 7
                }
            ),

        }

    def clean_proposal_document(self):

        document = self.cleaned_data.get(
            "proposal_document"
        )

        if document:

            if not document.name.lower().endswith(".pdf"):

                raise forms.ValidationError(
                    "Only PDF files are allowed."
                )

            if document.size > 10 * 1024 * 1024:

                raise forms.ValidationError(
                    "PDF file size must not exceed 10 MB."
                )

        return document