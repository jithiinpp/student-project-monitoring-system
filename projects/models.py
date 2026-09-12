from django.conf import settings
from django.db import models


class ProjectProposal(models.Model):

    STATUS_CHOICES = [
    ("SUBMITTED", "Submitted"),
    ("EXPERT_ASSIGNED", "Expert Assigned"),
    ("CHANGES_REQUESTED", "Changes Requested"),
    ("CHANGES_SENT_TO_STUDENT", "Changes Sent To Student"),
    ("EXPERT_APPROVED", "Expert Approved"),
    ("COORDINATOR_APPROVED", "Coordinator Approved"),
    ("GUIDE_ASSIGNED", "Guide Assigned"),
    ("GUIDE_REJECTED", "Guide Rejected"),
    ("IN_PROGRESS", "In Progress"),
    ("COMPLETED", "Completed"),
    ("REJECTED", "Rejected"),
]

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="project_proposals",
        limit_choices_to={"role": "STUDENT"},
    )

    title = models.CharField(max_length=255)

    abstract = models.TextField(blank=True)

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

    expert_comments = models.TextField(
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

    guide = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="guided_proposals",
        limit_choices_to={"role": "GUIDE"},
    )

    guide_rejection_reason = models.TextField(
        blank=True,
        null=True
    )

    guide_rejected_at = models.DateTimeField(
        blank=True,
        null=True
    )

    def __str__(self):
        return self.title


# =========================================================
# WEEKLY PROJECT PROGRESS
# =========================================================

class ProjectProgress(models.Model):

    STATUS_CHOICES = [
        ("SUBMITTED", "Submitted"),
        ("REVIEWED", "Reviewed"),
        ("CHANGES_REQUIRED", "Changes Required"),
    ]

    project = models.ForeignKey(
        ProjectProposal,
        on_delete=models.CASCADE,
        related_name="progress_reports"
    )

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="progress_reports",
        limit_choices_to={"role": "STUDENT"},
    )

    week_number = models.PositiveIntegerField()

    title = models.CharField(max_length=200)

    description = models.TextField()

    document = models.FileField(
        upload_to="progress_reports/",
        blank=True,
        null=True
    )

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="SUBMITTED"
    )

    guide_feedback = models.TextField(
        blank=True,
        null=True
    )

    submitted_at = models.DateTimeField(
        auto_now_add=True
    )

    reviewed_at = models.DateTimeField(
        blank=True,
        null=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["project", "week_number"],
                name="unique_project_week_progress"
            )
        ]

    def __str__(self):
        return f"{self.project.title} - Week {self.week_number}"


# =========================================================
# PROPOSAL CHANGE REQUEST
# =========================================================

class ProposalChangeRequest(models.Model):

    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("SENT_TO_STUDENT", "Sent to Student"),
        ("RESUBMITTED", "Resubmitted"),
        ("CLOSED", "Closed"),
    ]

    proposal = models.ForeignKey(
        ProjectProposal,
        on_delete=models.CASCADE,
        related_name="change_requests"
    )

    expert = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="requested_changes",
        limit_choices_to={"role": "EXPERT"}
    )

    coordinator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="forwarded_change_requests",
        limit_choices_to={"role": "COORDINATOR"}
    )

    message = models.TextField()

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="PENDING"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    sent_to_student_at = models.DateTimeField(
        blank=True,
        null=True
    )

    resubmitted_at = models.DateTimeField(
        blank=True,
        null=True
    )

    def __str__(self):
        return f"Change Request - {self.proposal.title}"