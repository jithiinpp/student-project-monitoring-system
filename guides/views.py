from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from projects.models import ProjectProposal, ProjectProgress

from .models import GuideEvaluation
from .forms import GuideEvaluationForm


# =========================================================
# GUIDE ACCESS CHECK
# =========================================================

def guide_required(view_func):

    @login_required
    def wrapper(request, *args, **kwargs):

        # Only Guide users can access Guide pages
        if request.user.role == "GUIDE":
            return view_func(request, *args, **kwargs)

        messages.error(
            request,
            "You are not authorized to access the Guide page."
        )

        return redirect("accounts:dashboard")

    return wrapper


# =========================================================
# GUIDE DASHBOARD
# =========================================================

@guide_required
def dashboard(request):

    assigned_projects = (
        ProjectProposal.objects
        .filter(
            guide=request.user
        )
        .select_related(
            "student",
            "domain_expert",
            "guide",
        )
        .order_by("-updated_at")
    )

    # Total assigned projects
    assigned_count = assigned_projects.count()

    # Guide rejected projects
    guide_rejected_count = assigned_projects.filter(
        status="GUIDE_REJECTED"
    ).count()

    # Projects currently in progress
    in_progress_count = assigned_projects.filter(
        status="IN_PROGRESS"
    ).count()

    # Completed projects
    completed_count = assigned_projects.filter(
        status="COMPLETED"
    ).count()

    # Final reports waiting for Guide review
    final_report_pending_count = ProjectProgress.objects.filter(
        project__guide=request.user,
        report_type="FINAL_REPORT",
        status="SUBMITTED",
    ).count()

    # Reports waiting for Guide review
    pending_reports_count = ProjectProgress.objects.filter(
        project__guide=request.user,
        status="SUBMITTED",
    ).count()

    return render(
        request,
        "guide/dashboard.html",
        {
            "assigned_projects": assigned_projects,
            "assigned_count": assigned_count,
            "guide_rejected_count": guide_rejected_count,
            "in_progress_count": in_progress_count,
            "completed_count": completed_count,
            "final_report_pending_count": final_report_pending_count,
            "pending_reports_count": pending_reports_count,
        }
    )


# =========================================================
# GUIDE ASSIGNED STUDENTS
# =========================================================

@guide_required
def students(request):

    assigned_projects = (
        ProjectProposal.objects
        .filter(
            guide=request.user
        )
        .select_related(
            "student",
            "domain_expert",
            "guide",
        )
        .order_by(
            "student__first_name",
            "student__last_name",
            "-updated_at",
        )
    )

    return render(
        request,
        "guide/students.html",
        {
            "assigned_projects": assigned_projects,
        }
    )


# =========================================================
# GUIDE PROJECT DETAIL
# =========================================================

@guide_required
def project_detail(request, proposal_id):

    proposal = get_object_or_404(
        ProjectProposal.objects.select_related(
            "student",
            "domain_expert",
            "guide",
        ),
        id=proposal_id,
        guide=request.user,
    )

    # -----------------------------------------------------
    # GET ALL STUDENT REPORTS
    # -----------------------------------------------------

    progress_reports = (
        ProjectProgress.objects
        .filter(
            project=proposal,
            student=proposal.student,
        )
        .order_by(
            "report_type"
        )
    )

    # -----------------------------------------------------
    # GET GUIDE FINAL EVALUATION
    # -----------------------------------------------------

    evaluation = (
        GuideEvaluation.objects
        .filter(
            project=proposal,
            guide=request.user,
        )
        .first()
    )

    # -----------------------------------------------------
    # EVALUATION FORM
    # -----------------------------------------------------

    if evaluation:

        evaluation_form = GuideEvaluationForm(
            instance=evaluation
        )

    else:

        evaluation_form = GuideEvaluationForm()

    # -----------------------------------------------------
    # CHECK FINAL REPORT
    # -----------------------------------------------------

    final_report = (
        ProjectProgress.objects
        .filter(
            project=proposal,
            student=proposal.student,
            report_type="FINAL_REPORT",
        )
        .first()
    )

    # -----------------------------------------------------
    # FINAL REPORT REVIEW STATUS
    # -----------------------------------------------------

    final_report_reviewed = False

    if final_report:

        if final_report.status == "REVIEWED":
            final_report_reviewed = True

    # -----------------------------------------------------
    # RENDER
    # -----------------------------------------------------

    return render(
        request,
        "guide/project_detail.html",
        {
            "proposal": proposal,
            "project": proposal,
            "progress_reports": progress_reports,
            "evaluation": evaluation,
            "evaluation_form": evaluation_form,
            "final_report": final_report,
            "final_report_reviewed": final_report_reviewed,
        }
    )


# =========================================================
# GUIDE REVIEW PROGRESS REPORT
# =========================================================

@guide_required
def review_progress(request, progress_id):

    progress = get_object_or_404(
        ProjectProgress.objects.select_related(
            "project",
            "student",
        ),
        id=progress_id,
        project__guide=request.user,
    )

    # -----------------------------------------------------
    # ONLY POST REQUEST ALLOWED
    # -----------------------------------------------------

    if request.method != "POST":

        return redirect(
            "guides:project_detail",
            proposal_id=progress.project.id,
        )

    # -----------------------------------------------------
    # GET REVIEW STATUS
    # -----------------------------------------------------

    review_status = request.POST.get(
        "status"
    )

    feedback = request.POST.get(
        "guide_feedback",
        ""
    ).strip()

    # -----------------------------------------------------
    # VALIDATE STATUS
    # -----------------------------------------------------

    if review_status not in [
        "REVIEWED",
        "CHANGES_REQUIRED",
    ]:

        messages.error(
            request,
            "Invalid review status."
        )

        return redirect(
            "guides:project_detail",
            proposal_id=progress.project.id,
        )

    # -----------------------------------------------------
    # FEEDBACK REQUIRED FOR CHANGES
    # -----------------------------------------------------

    if (
        review_status == "CHANGES_REQUIRED"
        and not feedback
    ):

        messages.error(
            request,
            "Please enter feedback when requesting changes."
        )

        return redirect(
            "guides:project_detail",
            proposal_id=progress.project.id,
        )

    # -----------------------------------------------------
    # UPDATE REPORT
    # -----------------------------------------------------

    progress.status = review_status

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
    # SUCCESS MESSAGE
    # -----------------------------------------------------

    if progress.report_type == "FINAL_REPORT":

        if review_status == "REVIEWED":

            messages.success(
                request,
                "Final Report has been reviewed successfully. You can now enter the final mark."
            )

        else:

            messages.success(
                request,
                "Changes have been requested for the Final Report."
            )

    else:

        if review_status == "REVIEWED":

            messages.success(
                request,
                f"{progress.get_report_type_display()} has been reviewed successfully."
            )

        else:

            messages.success(
                request,
                f"Changes requested for {progress.get_report_type_display()}."
            )

    return redirect(
        "guides:project_detail",
        proposal_id=progress.project.id,
    )


# =========================================================
# GUIDE EVALUATION / FINAL MARK
# =========================================================

@guide_required
def evaluate_project(request, proposal_id):

    proposal = get_object_or_404(
        ProjectProposal,
        id=proposal_id,
        guide=request.user,
    )

    # -----------------------------------------------------
    # ONLY POST REQUEST ALLOWED
    # -----------------------------------------------------

    if request.method != "POST":

        return redirect(
            "guides:project_detail",
            proposal_id=proposal.id,
        )

    # -----------------------------------------------------
    # CHECK FINAL REPORT
    # -----------------------------------------------------

    final_report = (
        ProjectProgress.objects
        .filter(
            project=proposal,
            student=proposal.student,
            report_type="FINAL_REPORT",
        )
        .first()
    )

    if not final_report:

        messages.error(
            request,
            "Final Report has not been submitted yet."
        )

        return redirect(
            "guides:project_detail",
            proposal_id=proposal.id,
        )

    # -----------------------------------------------------
    # FINAL REPORT MUST BE REVIEWED
    # -----------------------------------------------------

    if final_report.status != "REVIEWED":

        messages.error(
            request,
            "Please review and approve the Final Report before entering the final mark."
        )

        return redirect(
            "guides:project_detail",
            proposal_id=proposal.id,
        )

    # -----------------------------------------------------
    # GET EXISTING EVALUATION
    # -----------------------------------------------------

    evaluation = (
        GuideEvaluation.objects
        .filter(
            project=proposal,
            guide=request.user,
        )
        .first()
    )

    # -----------------------------------------------------
    # CREATE / UPDATE FORM
    # -----------------------------------------------------

    if evaluation:

        form = GuideEvaluationForm(
            request.POST,
            instance=evaluation,
        )

    else:

        form = GuideEvaluationForm(
            request.POST
        )

    # -----------------------------------------------------
    # SAVE FINAL MARK
    # -----------------------------------------------------

    if form.is_valid():

        evaluation = form.save(
            commit=False
        )

        evaluation.project = proposal

        evaluation.guide = request.user

        evaluation.save()

        # -------------------------------------------------
        # MARK PROJECT AS COMPLETED
        # -------------------------------------------------

        proposal.status = "COMPLETED"

        proposal.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        messages.success(
            request,
            "Final mark has been saved successfully. Student can now view the mark."
        )

        return redirect(
            "guides:project_detail",
            proposal_id=proposal.id,
        )

    # -----------------------------------------------------
    # FORM INVALID
    # -----------------------------------------------------

    progress_reports = (
        ProjectProgress.objects
        .filter(
            project=proposal,
            student=proposal.student,
        )
        .order_by(
            "report_type"
        )
    )

    return render(
        request,
        "guide/project_detail.html",
        {
            "proposal": proposal,
            "project": proposal,
            "progress_reports": progress_reports,
            "evaluation": evaluation,
            "evaluation_form": form,
            "final_report": final_report,
            "final_report_reviewed": True,
        }
    )


# =========================================================
# GUIDE REJECT PROJECT
# =========================================================

@guide_required
def reject_project(request, proposal_id):

    proposal = get_object_or_404(
        ProjectProposal,
        id=proposal_id,
        guide=request.user,
    )

    # -----------------------------------------------------
    # ONLY POST REQUEST
    # -----------------------------------------------------

    if request.method != "POST":

        return redirect(
            "guides:project_detail",
            proposal_id=proposal.id,
        )

    # -----------------------------------------------------
    # GUIDE CAN REJECT ONLY GUIDE_ASSIGNED PROJECT
    # -----------------------------------------------------

    if proposal.status != "GUIDE_ASSIGNED":

        messages.error(
            request,
            "This project cannot be rejected at its current stage."
        )

        return redirect(
            "guides:project_detail",
            proposal_id=proposal.id,
        )

    # -----------------------------------------------------
    # REJECT PROJECT
    # -----------------------------------------------------

    proposal.status = "GUIDE_REJECTED"

    proposal.guide_rejected_at = timezone.now()

    proposal.save(
        update_fields=[
            "status",
            "guide_rejected_at",
            "updated_at",
        ]
    )

    messages.success(
        request,
        "Project has been rejected by the Guide."
    )

    return redirect(
        "guides:dashboard"
    )


# =========================================================
# GUIDE ACCEPT / START PROJECT
# =========================================================

@guide_required
def start_project(request, proposal_id):

    proposal = get_object_or_404(
        ProjectProposal,
        id=proposal_id,
        guide=request.user,
    )

    # -----------------------------------------------------
    # ONLY POST REQUEST
    # -----------------------------------------------------

    if request.method != "POST":

        return redirect(
            "guides:project_detail",
            proposal_id=proposal.id,
        )

    # -----------------------------------------------------
    # PROJECT MUST BE GUIDE_ASSIGNED
    # -----------------------------------------------------

    if proposal.status != "GUIDE_ASSIGNED":

        messages.error(
            request,
            "This project cannot be started at the current stage."
        )

        return redirect(
            "guides:project_detail",
            proposal_id=proposal.id,
        )

    # -----------------------------------------------------
    # START PROJECT
    # -----------------------------------------------------

    proposal.status = "IN_PROGRESS"

    proposal.save(
        update_fields=[
            "status",
            "updated_at",
        ]
    )

    messages.success(
        request,
        "Project has been accepted and moved to In Progress."
    )

    return redirect(
        "guides:project_detail",
        proposal_id=proposal.id,
    )