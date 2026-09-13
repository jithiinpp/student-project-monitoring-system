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
                    "placeholder": "Enter marks out of 100",
                    "min": "0",
                    "max": "100",
                    "step": "0.01",
                }
            ),

            "feedback": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter evaluation feedback...",
                    "rows": 6,
                }
            ),
        }

    def clean_marks(self):

        marks = self.cleaned_data["marks"]

        if marks < 0 or marks > 100:

            raise forms.ValidationError(
                "Marks must be between 0 and 100."
            )

        return marks