from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from projects.models import (
    ProjectProposal,
    ProjectProgress,
)

from .models import GuideEvaluation
from .forms import GuideEvaluationForm


# =========================================================
# GUIDE ACCESS CHECK
# =========================================================

def guide_required(view_func):

    @login_required
    def wrapper(request, *args, **kwargs):

        if request.user.role != "GUIDE":

            messages.error(
                request,
                "You are not authorized to access Guide pages."
            )

            return redirect(
                "accounts:dashboard"
            )

        return view_func(
            request,
            *args,
            **kwargs
        )

    return wrapper


# =========================================================
# GUIDE DASHBOARD
# =========================================================

@guide_required
def dashboard(request):

    projects = ProjectProposal.objects.filter(
        guide=request.user
    ).select_related(
        "student"
    ).order_by(
        "-updated_at"
    )

    assigned_count = projects.count()

    rejected_count = projects.filter(
        status="GUIDE_REJECTED"
    ).count()

    in_progress_count = projects.filter(
        status="IN_PROGRESS"
    ).count()

    completed_count = projects.filter(
        status="COMPLETED"
    ).count()

    # -----------------------------------------------------
    # FINAL REPORTS WAITING FOR REVIEW
    # -----------------------------------------------------

    final_reports_pending = ProjectProgress.objects.filter(
        project__guide=request.user,
        report_type="FINAL_REPORT",
        status="SUBMITTED"
    ).count()

    # -----------------------------------------------------
    # ALL REPORTS WAITING FOR REVIEW
    # -----------------------------------------------------

    reports_pending = ProjectProgress.objects.filter(
        project__guide=request.user,
        status="SUBMITTED"
    ).count()

    return render(
        request,
        "guide/dashboard.html",
        {
            "projects": projects,

            "assigned_count": assigned_count,
            "rejected_count": rejected_count,
            "in_progress_count": in_progress_count,
            "completed_count": completed_count,

            "final_reports_pending": final_reports_pending,
            "reports_pending": reports_pending,
        }
    )


# =========================================================
# GUIDE STUDENTS
# =========================================================

@guide_required
def students(request):

    projects = ProjectProposal.objects.filter(
        guide=request.user
    ).select_related(
        "student"
    ).order_by(
        "-updated_at"
    )

    return render(
        request,
        "guide/students.html",
        {
            "projects": projects
        }
    )


# =========================================================
# PROJECT DETAIL
# =========================================================

@guide_required
def project_detail(request, proposal_id):

    project = get_object_or_404(
        ProjectProposal,
        id=proposal_id,
        guide=request.user
    )

    # -----------------------------------------------------
    # WEEKLY REPORTS
    # -----------------------------------------------------

    weekly_reports = ProjectProgress.objects.filter(
        project=project,
        student=project.student,
        report_type="WEEKLY_PROGRESS"
    ).order_by(
        "submitted_at"
    )

    # -----------------------------------------------------
    # FINAL REPORT
    # -----------------------------------------------------

    final_report = ProjectProgress.objects.filter(
        project=project,
        student=project.student,
        report_type="FINAL_REPORT"
    ).first()

    # -----------------------------------------------------
    # GUIDE EVALUATION
    # -----------------------------------------------------

    evaluation = GuideEvaluation.objects.filter(
        project=project
    ).first()

    # -----------------------------------------------------
    # WEEKLY REPORT COUNTS
    # -----------------------------------------------------

    weekly_count = weekly_reports.count()

    reviewed_weekly_count = weekly_reports.filter(
        status="REVIEWED"
    ).count()

    all_weekly_reviewed = (
        weekly_count > 0
        and reviewed_weekly_count == weekly_count
    )

    # -----------------------------------------------------
    # FINAL REPORT REVIEW STATUS
    # -----------------------------------------------------

    final_report_reviewed = (
        final_report is not None
        and final_report.status == "REVIEWED"
    )

    # -----------------------------------------------------
    # CAN ENTER FINAL MARK
    # -----------------------------------------------------

    can_evaluate = (
        final_report is not None
        and final_report_reviewed
        and all_weekly_reviewed
    )

    return render(
        request,
        "guide/project_detail.html",
        {
            "project": project,

            "weekly_reports": weekly_reports,
            "final_report": final_report,

            "weekly_count": weekly_count,
            "reviewed_weekly_count": reviewed_weekly_count,
            "all_weekly_reviewed": all_weekly_reviewed,

            "final_report_reviewed": final_report_reviewed,

            "evaluation": evaluation,

            "can_evaluate": can_evaluate,
        }
    )


# =========================================================
# REVIEW PROGRESS REPORT
# =========================================================

@guide_required
def review_progress(request, progress_id):

    progress = get_object_or_404(
        ProjectProgress,
        id=progress_id,
        project__guide=request.user
    )

    if request.method != "POST":

        return redirect(
            "guides:project_detail",
            proposal_id=progress.project.id
        )

    status = request.POST.get(
        "status"
    )

    feedback = request.POST.get(
        "guide_feedback",
        ""
    ).strip()

    # -----------------------------------------------------
    # VALID STATUS
    # -----------------------------------------------------

    if status not in [
        "REVIEWED",
        "CHANGES_REQUIRED",
    ]:

        messages.error(
            request,
            "Invalid review status."
        )

        return redirect(
            "guides:project_detail",
            proposal_id=progress.project.id
        )

    # -----------------------------------------------------
    # SAVE REVIEW
    # -----------------------------------------------------

    progress.status = status

    progress.guide_feedback = feedback

    progress.reviewed_at = timezone.now()

    progress.save(
        update_fields=[
            "status",
            "guide_feedback",
            "reviewed_at",
        ]
    )

    # -----------------------------------------------------
    # FINAL REPORT
    # -----------------------------------------------------

    if progress.report_type == "FINAL_REPORT":

        if status == "REVIEWED":

            messages.success(
                request,
                "Final report reviewed successfully. "
                "You can enter the final mark if all weekly "
                "reports are also reviewed."
            )

        else:

            messages.warning(
                request,
                "Final report marked as changes required."
            )

    # -----------------------------------------------------
    # WEEKLY REPORT
    # -----------------------------------------------------

    else:

        if status == "REVIEWED":

            messages.success(
                request,
                "Weekly progress report reviewed successfully."
            )

        else:

            messages.warning(
                request,
                "Weekly progress report marked as changes required."
            )

    return redirect(
        "guides:project_detail",
        proposal_id=progress.project.id
    )


# =========================================================
# EVALUATE PROJECT
# =========================================================

@guide_required
def evaluate_project(request, proposal_id):

    project = get_object_or_404(
        ProjectProposal,
        id=proposal_id,
        guide=request.user
    )

    # -----------------------------------------------------
    # FINAL REPORT
    # -----------------------------------------------------

    final_report = ProjectProgress.objects.filter(
        project=project,
        student=project.student,
        report_type="FINAL_REPORT"
    ).first()

    if final_report is None:

        messages.error(
            request,
            "Student has not submitted the final report yet."
        )

        return redirect(
            "guides:project_detail",
            proposal_id=project.id
        )

    # -----------------------------------------------------
    # FINAL REPORT MUST BE REVIEWED
    # -----------------------------------------------------

    if final_report.status != "REVIEWED":

        messages.error(
            request,
            "Final report must be reviewed before entering final marks."
        )

        return redirect(
            "guides:project_detail",
            proposal_id=project.id
        )

    # -----------------------------------------------------
    # ALL WEEKLY REPORTS
    # -----------------------------------------------------

    weekly_reports = ProjectProgress.objects.filter(
        project=project,
        student=project.student,
        report_type="WEEKLY_PROGRESS"
    )

    weekly_count = weekly_reports.count()

    reviewed_weekly_count = weekly_reports.filter(
        status="REVIEWED"
    ).count()

    # -----------------------------------------------------
    # AT LEAST ONE WEEKLY REPORT
    # -----------------------------------------------------

    if weekly_count == 0:

        messages.error(
            request,
            "Student must have weekly progress reports "
            "before final evaluation."
        )

        return redirect(
            "guides:project_detail",
            proposal_id=project.id
        )

    # -----------------------------------------------------
    # ALL WEEKLY REPORTS MUST BE REVIEWED
    # -----------------------------------------------------

    if reviewed_weekly_count != weekly_count:

        messages.error(
            request,
            "All weekly progress reports must be reviewed "
            "before entering the final mark."
        )

        return redirect(
            "guides:project_detail",
            proposal_id=project.id
        )

    # -----------------------------------------------------
    # EXISTING EVALUATION
    # -----------------------------------------------------

    evaluation = GuideEvaluation.objects.filter(
        project=project
    ).first()

    # -----------------------------------------------------
    # POST
    # -----------------------------------------------------

    if request.method == "POST":

        if evaluation:

            form = GuideEvaluationForm(
                request.POST,
                instance=evaluation
            )

        else:

            form = GuideEvaluationForm(
                request.POST
            )

        if form.is_valid():

            evaluation = form.save(
                commit=False
            )

            evaluation.project = project

            evaluation.guide = request.user

            evaluation.save()

            # ---------------------------------------------
            # MARK PROJECT COMPLETED
            # ---------------------------------------------

            project.status = "COMPLETED"

            project.save(
                update_fields=["status"]
            )

            messages.success(
                request,
                "Final mark saved successfully. "
                "Project marked as completed."
            )

            return redirect(
                "guides:project_detail",
                proposal_id=project.id
            )

    else:

        if evaluation:

            form = GuideEvaluationForm(
                instance=evaluation
            )

        else:

            form = GuideEvaluationForm()

    return render(
        request,
        "guide/project_detail.html",
        {
            "project": project,

            "weekly_reports": weekly_reports,
            "final_report": final_report,

            "weekly_count": weekly_count,
            "reviewed_weekly_count": reviewed_weekly_count,

            "all_weekly_reviewed": (
                weekly_count > 0
                and reviewed_weekly_count == weekly_count
            ),

            "final_report_reviewed": True,

            "evaluation": evaluation,

            "can_evaluate": True,

            "evaluation_form": form,
        }
    )


# =========================================================
# START PROJECT
# =========================================================

@guide_required
def start_project(request, proposal_id):

    project = get_object_or_404(
        ProjectProposal,
        id=proposal_id,
        guide=request.user
    )

    if project.status != "GUIDE_ASSIGNED":

        messages.error(
            request,
            "This project cannot be started."
        )

        return redirect(
            "guides:project_detail",
            proposal_id=project.id
        )

    project.status = "IN_PROGRESS"

    project.save(
        update_fields=["status"]
    )

    messages.success(
        request,
        "Project started successfully."
    )

    return redirect(
        "guides:project_detail",
        proposal_id=project.id
    )


# =========================================================
# REJECT PROJECT
# =========================================================

@guide_required
def reject_project(request, proposal_id):

    project = get_object_or_404(
        ProjectProposal,
        id=proposal_id,
        guide=request.user
    )

    if project.status != "GUIDE_ASSIGNED":

        messages.error(
            request,
            "This project cannot be rejected at this stage."
        )

        return redirect(
            "guides:project_detail",
            proposal_id=project.id
        )

    if request.method == "POST":

        reason = request.POST.get(
            "guide_rejection_reason",
            ""
        ).strip()

        if not reason:

            messages.error(
                request,
                "Please enter a rejection reason."
            )

            return redirect(
                "guides:project_detail",
                proposal_id=project.id
            )

        project.status = "GUIDE_REJECTED"

        project.guide_rejection_reason = reason

        project.guide_rejected_at = timezone.now()

        project.save(
            update_fields=[
                "status",
                "guide_rejection_reason",
                "guide_rejected_at",
            ]
        )

        messages.success(
            request,
            "Project rejected successfully."
        )

    return redirect(
        "guides:students"
    )