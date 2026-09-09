from django.conf import settings
from django.db import models


# ============================================================
# PROJECT PROPOSAL
# ============================================================

class ProjectProposal(models.Model):

    STATUS_CHOICES = [
        ("SUBMITTED", "Submitted"),
        ("EXPERT_ASSIGNED", "Expert Assigned"),
        ("CHANGES_REQUESTED", "Changes Requested"),
        ("EXPERT_APPROVED", "Expert Approved"),
        ("COORDINATOR_APPROVED", "Coordinator Approved"),
        ("GUIDE_ASSIGNED", "Guide Assigned"),
        ("IN_PROGRESS", "In Progress"),
        ("COMPLETED", "Completed"),
    ]

    # --------------------------------------------------------
    # STUDENT
    # --------------------------------------------------------

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="project_proposals",
        limit_choices_to={"role": "STUDENT"},
    )

    # --------------------------------------------------------
    # PROJECT DETAILS
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # PROPOSAL DOCUMENT
    # --------------------------------------------------------

    proposal_document = models.FileField(
        upload_to="proposals/",
        blank=True,
        null=True
    )

    # --------------------------------------------------------
    # STATUS
    # --------------------------------------------------------

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="SUBMITTED"
    )

    # --------------------------------------------------------
    # DATES
    # --------------------------------------------------------

    submitted_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    # --------------------------------------------------------
    # DOMAIN EXPERT
    # --------------------------------------------------------

    domain_expert = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="expert_proposals",
        limit_choices_to={"role": "EXPERT"},
    )

    # --------------------------------------------------------
    # GUIDE
    # --------------------------------------------------------

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


# ============================================================
# WEEKLY PROJECT PROGRESS
# ============================================================

class ProjectProgress(models.Model):

    STATUS_CHOICES = [
        ("SUBMITTED", "Submitted"),
        ("REVIEWED", "Reviewed"),
        ("CHANGES_REQUIRED", "Changes Required"),
    ]

    # --------------------------------------------------------
    # PROJECT
    # --------------------------------------------------------

    project = models.ForeignKey(
        ProjectProposal,
        on_delete=models.CASCADE,
        related_name="progress_reports"
    )

    # --------------------------------------------------------
    # STUDENT
    # --------------------------------------------------------

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="progress_reports",
        limit_choices_to={"role": "STUDENT"},
    )

    # --------------------------------------------------------
    # WEEK NUMBER
    # --------------------------------------------------------

    week_number = models.PositiveIntegerField()

    # --------------------------------------------------------
    # PROGRESS TITLE
    # --------------------------------------------------------

    title = models.CharField(
        max_length=200
    )

    # --------------------------------------------------------
    # DESCRIPTION
    # --------------------------------------------------------

    description = models.TextField()

    # --------------------------------------------------------
    # PROGRESS DOCUMENT
    # --------------------------------------------------------

    document = models.FileField(
        upload_to="progress_reports/",
        blank=True,
        null=True
    )

    # --------------------------------------------------------
    # STATUS
    # --------------------------------------------------------

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="SUBMITTED"
    )

    # --------------------------------------------------------
    # GUIDE FEEDBACK
    # --------------------------------------------------------

    guide_feedback = models.TextField(
        blank=True,
        null=True
    )

    # --------------------------------------------------------
    # DATES
    # --------------------------------------------------------

    submitted_at = models.DateTimeField(
        auto_now_add=True
    )

    reviewed_at = models.DateTimeField(
        blank=True,
        null=True
    )

    def __str__(self):
        return f"{self.project.title} - Week {self.week_number}"