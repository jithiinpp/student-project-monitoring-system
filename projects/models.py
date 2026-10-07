from django.conf import settings
from django.db import models


# =========================================================
# PROJECT PROPOSAL
# =========================================================
class ProjectProposal(models.Model):

    PROJECT_TYPE_CHOICES = [
        ("MINI", "Mini Project"),
        ("MAIN", "Main Project"),
    ]

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
        limit_choices_to={"is_student": True}
    )

    # NEW
    project_type = models.CharField(
        max_length=10,
        choices=PROJECT_TYPE_CHOICES,
        default="MAIN"
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

    domain_expert = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="expert_proposals",
        limit_choices_to={"is_expert": True}
    )

    expert_comments = models.TextField(
        blank=True,
        null=True
    )

    status = models.CharField(
        max_length=40,
        choices=STATUS_CHOICES,
        default="SUBMITTED"
    )

    guide = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="guided_proposals",
        limit_choices_to={"is_guide": True}
    )

    guide_rejection_reason = models.TextField(
        blank=True,
        null=True
    )

    guide_rejected_at = models.DateTimeField(
        blank=True,
        null=True
    )

    review_date = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Scheduled date and time for the project review by the panel."
    )

    submitted_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return self.title


# =========================================================
# PROPOSAL CHANGE REQUEST
# =========================================================

class ProposalChangeRequest(models.Model):

    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("SENT_TO_STUDENT", "Sent To Student"),
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
        on_delete=models.CASCADE,
        related_name="proposal_change_requests",
        limit_choices_to={"is_expert": True}
    )

    comments = models.TextField()

    coordinator_comments = models.TextField(
        blank=True,
        null=True
    )

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="PENDING"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return (
            f"Change Request - "
            f"{self.proposal.title}"
        )


# =========================================================
# PROJECT PROGRESS
# =========================================================

class ProjectProgress(models.Model):

    REPORT_CHOICES = [
        (
            "PROGRESS_1",
            "Progress Report 1"
        ),
        (
            "PROGRESS_2",
            "Progress Report 2"
        ),
        (
            "PROGRESS_3",
            "Progress Report 3"
        ),
        (
            "FINAL_REPORT",
            "Final Report"
        ),
    ]

    STATUS_CHOICES = [
        (
            "SUBMITTED",
            "Submitted"
        ),
        (
            "REVIEWED",
            "Reviewed"
        ),
        (
            "CHANGES_REQUIRED",
            "Changes Required"
        ),
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
        limit_choices_to={
            "is_student": True
        }
    )

    report_type = models.CharField(
        max_length=30,
        choices=REPORT_CHOICES
    )

    week_number = models.PositiveSmallIntegerField(
        blank=True,
        null=True
    )

    title = models.CharField(
        max_length=200
    )

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

    marks = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )

    detailed_marks = models.JSONField(
        default=dict,
        blank=True
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
        ordering = [
            "submitted_at"
        ]

    def __str__(self):

        return (
            f"{self.project.title} - "
            f"{self.get_report_type_display()}"
        )

    @property
    def week_label(self):
        week_number = self.week_number
        if week_number is None:
            week_number = {
                "PROGRESS_1": 1,
                "PROGRESS_2": 2,
                "PROGRESS_3": 3,
            }.get(self.report_type)
        return f"Week {week_number}" if week_number else ""


# =========================================================
# PANEL EVALUATION
# =========================================================

class PanelEvaluation(models.Model):

    project = models.OneToOneField(
        ProjectProposal,
        on_delete=models.CASCADE,
        related_name="panel_evaluation"
    )

    panel_member = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="panel_evaluations",
        limit_choices_to={"is_panel": True}
    )

    marks = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )

    detailed_marks = models.JSONField(
        default=dict,
        blank=True
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
        return f"Panel Evaluation for {self.project.title}"


# =========================================================
# PROJECT MESSAGES
# =========================================================

class ProjectMessage(models.Model):
    project = models.ForeignKey(
        ProjectProposal,
        on_delete=models.CASCADE,
        related_name="messages"
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_messages"
    )
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Message by {self.sender.username} on {self.project.title}"