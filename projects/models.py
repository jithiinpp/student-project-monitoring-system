from django.conf import settings
from django.db import models


# =========================================================
# PROJECT PROPOSAL
# =========================================================

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

    # -----------------------------------------------------
    # STUDENT
    # -----------------------------------------------------

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="project_proposals",
        limit_choices_to={"role": "STUDENT"},
    )

    # -----------------------------------------------------
    # PROJECT INFORMATION
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # DOMAIN EXPERT
    # -----------------------------------------------------

    domain_expert = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="expert_proposals",
        limit_choices_to={"role": "EXPERT"},
    )

    expert_comments = models.TextField(
        blank=True,
        null=True
    )

    # -----------------------------------------------------
    # PROJECT STATUS
    # -----------------------------------------------------

    status = models.CharField(
        max_length=40,
        choices=STATUS_CHOICES,
        default="SUBMITTED"
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

    guide_rejection_reason = models.TextField(
        blank=True,
        null=True
    )

    guide_rejected_at = models.DateTimeField(
        blank=True,
        null=True
    )

    # -----------------------------------------------------
    # TIMESTAMPS
    # -----------------------------------------------------

    submitted_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    # -----------------------------------------------------
    # STRING REPRESENTATION
    # -----------------------------------------------------

    def __str__(self):
        return self.title


# =========================================================
# PROJECT PROGRESS / FINAL REPORT
# =========================================================

class ProjectProgress(models.Model):

    REPORT_CHOICES = [
        ("PROGRESS_1", "Progress Report 1"),
        ("PROGRESS_2", "Progress Report 2"),
        ("PROGRESS_3", "Progress Report 3"),
        ("FINAL_REPORT", "Final Report"),
    ]

    STATUS_CHOICES = [
        ("SUBMITTED", "Submitted"),
        ("REVIEWED", "Reviewed"),
        ("CHANGES_REQUIRED", "Changes Required"),
    ]

    # -----------------------------------------------------
    # PROJECT
    # -----------------------------------------------------

    project = models.ForeignKey(
        ProjectProposal,
        on_delete=models.CASCADE,
        related_name="progress_reports"
    )

    # -----------------------------------------------------
    # STUDENT
    # -----------------------------------------------------

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="progress_reports",
        limit_choices_to={"role": "STUDENT"}
    )

    # -----------------------------------------------------
    # REPORT TYPE
    # -----------------------------------------------------

    report_type = models.CharField(
        max_length=30,
        choices=REPORT_CHOICES
    )

    # -----------------------------------------------------
    # REPORT DETAILS
    # -----------------------------------------------------

    title = models.CharField(
        max_length=200
    )

    description = models.TextField()

    document = models.FileField(
        upload_to="progress_reports/",
        blank=True,
        null=True
    )

    # -----------------------------------------------------
    # GUIDE REVIEW STATUS
    # -----------------------------------------------------

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="SUBMITTED"
    )

    guide_feedback = models.TextField(
        blank=True,
        null=True
    )

    # -----------------------------------------------------
    # TIMESTAMPS
    # -----------------------------------------------------

    submitted_at = models.DateTimeField(
        auto_now_add=True
    )

    reviewed_at = models.DateTimeField(
        blank=True,
        null=True
    )

    # -----------------------------------------------------
    # PREVENT DUPLICATE REPORTS
    # -----------------------------------------------------

    class Meta:

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "project",
                    "report_type"
                ],
                name="unique_project_report_type"
            )
        ]

        ordering = [
            "submitted_at"
        ]

    # -----------------------------------------------------
    # STRING REPRESENTATION
    # -----------------------------------------------------

    def __str__(self):
        return (
            f"{self.project.title} - "
            f"{self.get_report_type_display()}"
        )


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

    # -----------------------------------------------------
    # PROPOSAL
    # -----------------------------------------------------

    proposal = models.ForeignKey(
        ProjectProposal,
        on_delete=models.CASCADE,
        related_name="change_requests"
    )

    # -----------------------------------------------------
    # DOMAIN EXPERT
    # -----------------------------------------------------

    expert = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="requested_changes",
        limit_choices_to={"role": "EXPERT"}
    )

    # -----------------------------------------------------
    # COORDINATOR
    # -----------------------------------------------------

    coordinator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="forwarded_change_requests",
        limit_choices_to={"role": "COORDINATOR"}
    )

    # -----------------------------------------------------
    # CHANGE REQUEST MESSAGE
    # -----------------------------------------------------

    message = models.TextField()

    # -----------------------------------------------------
    # STATUS
    # -----------------------------------------------------

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="PENDING"
    )

    # -----------------------------------------------------
    # TIMESTAMPS
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # STRING REPRESENTATION
    # -----------------------------------------------------

    def __str__(self):
        return (
            f"Change Request - "
            f"{self.proposal.title}"
        )