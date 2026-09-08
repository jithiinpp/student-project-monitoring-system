from django.conf import settings
from django.db import models


class ProjectProposal(models.Model):

    STATUS_CHOICES = [
        ("SUBMITTED", "Submitted"),
        ("EXPERT_ASSIGNED", "Expert Assigned"),
        ("EXPERT_APPROVED", "Expert Approved"),
        ("COORDINATOR_APPROVED", "Coordinator Approved"),
        ("GUIDE_ASSIGNED", "Guide Assigned"),
        ("IN_PROGRESS", "In Progress"),
        ("COMPLETED", "Completed"),
    ]

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="project_proposals",
        limit_choices_to={"role": "STUDENT"},
    )

    title = models.CharField(
        max_length=255
    )

    abstract = models.TextField(
        blank=True
    )

    domain = models.CharField(
        max_length=255,
        blank=True
    )

    technologies = models.TextField(
        blank=True
    )

    description = models.TextField(
        blank=True
    )

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
        null=True,
        blank=True,
        related_name="expert_proposals",
        limit_choices_to={"role": "EXPERT"},
    )

    # -----------------------------------------------------
    # GUIDE
    # -----------------------------------------------------

    guide = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="guided_proposals",
        limit_choices_to={"role": "GUIDE"},
    )

    def __str__(self):
        return self.title