from django import forms

from .models import GuideEvaluation


class GuideEvaluationForm(forms.ModelForm):

    class Meta:

        model = GuideEvaluation

        fields = [
            "marks",
            "feedback",
        ]

        widgets = {

            "marks": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter final mark",
                    "min": "0",
                    "max": "100",
                    "step": "0.01",
                }
            ),

            "feedback": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter final feedback",
                    "rows": 5,
                }
            ),
        }

        labels = {
            "marks": "Final Mark",
            "feedback": "Final Feedback",
        }

    def clean_marks(self):

        marks = self.cleaned_data.get("marks")

        if marks is None:
            raise forms.ValidationError(
                "Please enter the final mark."
            )

        if marks < 0 or marks > 100:
            raise forms.ValidationError(
                "Final mark must be between 0 and 100."
            )

        return marks