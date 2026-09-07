from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class ProjectProposal(models.Model):

    STATUS_CHOICES = [
        ("SUBMITTED", "Submitted"),
        ("EXPERT_ASSIGNED", "Expert Assigned"),
        ("EXPERT_APPROVED", "Expert Approved"),
        ("CHANGES_REQUESTED", "Changes Requested"),
        ("COORDINATOR_APPROVED", "Coordinator Approved"),
        ("REJECTED", "Rejected"),
    ]

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="project_proposals",
        limit_choices_to={"role": "STUDENT"},
    )

    title = models.CharField(
        max_length=200
    )

    abstract = models.TextField()

    domain = models.CharField(
        max_length=100
    )

    technologies = models.CharField(
        max_length=500
    )

    description = models.TextField()

    proposal_document = models.FileField(
        upload_to="proposals/",
        blank=True,
        null=True
    )

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="SUBMITTED"
    )

    submitted_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )
    domain_expert = models.ForeignKey(
    settings.AUTH_USER_MODEL,
    on_delete=models.SET_NULL,
    related_name="assigned_proposals",
    blank=True,
    null=True,
    limit_choices_to={"role": "EXPERT"},
)
    def clean(self):

        if self.student_id:

            existing_count = ProjectProposal.objects.filter(
                student=self.student
            ).exclude(
                pk=self.pk
            ).count()

            if existing_count >= 3:

                raise ValidationError(
                    "A student can submit a maximum of 3 proposals."
                )

    def __str__(self):

        return f"{self.title} - {self.student.username}"

    class Meta:

        ordering = [
            "-submitted_at"
        ]