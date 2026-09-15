from django.conf import settings
from django.db import models


class GuideEvaluation(models.Model):

    project = models.OneToOneField(
        "projects.ProjectProposal",
        on_delete=models.CASCADE,
        related_name="guide_evaluation"
    )

    guide = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="guide_evaluations",
        limit_choices_to={
            "role": "GUIDE"
        }
    )

    marks = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )

    feedback = models.TextField(
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):

        return (
            f"{self.project.title} - "
            f"{self.marks}/100"
        )