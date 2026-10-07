from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.db.models import Q

from projects.models import (
    ProjectProposal,
    ProjectProgress,
    ProjectMessage,
)

from .models import GuideEvaluation
from .forms import GuideEvaluationForm


# =========================================================
# GUIDE ACCESS CHECK
# =========================================================

def guide_required(view_func):

    @login_required
    def wrapper(request, *args, **kwargs):

        if not request.user.is_guide:

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

    # -----------------------------------------------------
    # PROJECTS ASSIGNED TO THIS GUIDE
    # -----------------------------------------------------

    projects = (
        ProjectProposal.objects
        .filter(
            guide=request.user
        )
        .select_related(
            "student"
        )
        .order_by(
            "-updated_at"
        )
    )

    # -----------------------------------------------------
    # PROJECT COUNTS
    # -----------------------------------------------------

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
    # REPORTS WAITING FOR REVIEW
    # -----------------------------------------------------

    reports_pending = (
        ProjectProgress.objects
        .filter(
            project__guide=request.user,
            status="SUBMITTED"
        )
        .count()
    )

    proposals_pending = projects.filter(status="GUIDE_ASSIGNED").count()
    total_pending = reports_pending + proposals_pending

    # -----------------------------------------------------
    # FINAL REPORTS WAITING FOR REVIEW
    # -----------------------------------------------------

    final_reports_pending = (
        ProjectProgress.objects
        .filter(
            project__guide=request.user,
            report_type="FINAL_REPORT",
            status="SUBMITTED"
        )
        .count()
    )

    # -----------------------------------------------------
    # WEEKLY REPORTS WAITING FOR REVIEW
    # -----------------------------------------------------

    weekly_reports_pending = (
        ProjectProgress.objects
        .filter(
            project__guide=request.user,
            report_type__in=["PROGRESS_1", "PROGRESS_2", "PROGRESS_3"],
            status="SUBMITTED"
        )
        .count()
    )

    # -----------------------------------------------------
    # TOTAL WEEKLY REPORTS
    # -----------------------------------------------------

    weekly_reports_count = (
        ProjectProgress.objects
        .filter(
            project__guide=request.user,
            report_type__in=["PROGRESS_1", "PROGRESS_2", "PROGRESS_3"]
        )
        .count()
    )

    # -----------------------------------------------------
    # TOTAL FINAL REPORTS
    # -----------------------------------------------------

    final_reports_count = (
        ProjectProgress.objects
        .filter(
            project__guide=request.user,
            report_type="FINAL_REPORT"
        )
        .count()
    )

    # -----------------------------------------------------
    # SCHEDULED REVIEWS
    # -----------------------------------------------------

    scheduled_reviews = projects.exclude(review_date__isnull=True).order_by("review_date")

    # -----------------------------------------------------
    # SEND DATA TO TEMPLATE
    # -----------------------------------------------------

    return render(
        request,
        "guide/dashboard.html",
        {
            "projects": projects,
            "scheduled_reviews": scheduled_reviews,

            "assigned_count": assigned_count,
            "rejected_count": rejected_count,
            "in_progress_count": in_progress_count,
            "completed_count": completed_count,

            "reports_pending": total_pending,
            "weekly_reports_pending": weekly_reports_pending,
            "final_reports_pending": final_reports_pending,

            "weekly_reports_count": weekly_reports_count,
            "final_reports_count": final_reports_count,
        }
    )


# =========================================================
# GUIDE STUDENTS
# =========================================================

@guide_required
def students(request):

    projects = (
        ProjectProposal.objects
        .filter(
            guide=request.user
        )
        .select_related(
            "student"
        )
        .order_by(
            "-updated_at"
        )
    )

    status_filter = request.GET.get('status')
    if status_filter:
        if status_filter == "PENDING_REVIEW":
            projects = projects.filter(
                Q(progress_reports__status="SUBMITTED") | Q(status="GUIDE_ASSIGNED")
            ).distinct()
        else:
            projects = projects.filter(status=status_filter)

    return render(
        request,
        "guide/students.html",
        {
            "projects": projects
        }
    )


@login_required
@guide_required
def reports(request):
    all_reports = (
        ProjectProgress.objects
        .filter(
            project__guide=request.user
        )
        .select_related("project", "project__student")
        .order_by("project", "-submitted_at")
    )
    return render(request, "guide/reports.html", {
        "reports": all_reports,
        "page_title": "Reports"
    })


@login_required
@guide_required
def evaluations(request):
    projects = ProjectProposal.objects.filter(
        guide=request.user,
        progress_reports__report_type="FINAL_REPORT"
    ).select_related(
        "student"
    ).distinct()
    
    return render(request, "guide/evaluations.html", {
        "projects": projects
    })


# =========================================================
# PROJECT DETAIL
# =========================================================

@guide_required
def project_detail(request, proposal_id):

    # -----------------------------------------------------
    # ONLY SHOW PROJECTS ASSIGNED TO THIS GUIDE
    # -----------------------------------------------------

    project = get_object_or_404(
        ProjectProposal,
        id=proposal_id,
        guide=request.user
    )

    # -----------------------------------------------------
    # MESSAGES
    # -----------------------------------------------------

    project_messages = project.messages.select_related("sender").all()

    # -----------------------------------------------------
    # WEEKLY REPORTS
    # -----------------------------------------------------

    weekly_reports = (
        ProjectProgress.objects
        .filter(
            project=project,
            student=project.student,
            report_type__in=["PROGRESS_1", "PROGRESS_2", "PROGRESS_3"]
        )
        .order_by(
            "submitted_at"
        )
    )

    # -----------------------------------------------------
    # FINAL REPORT
    # -----------------------------------------------------

    final_report = (
        ProjectProgress.objects
        .filter(
            project=project,
            student=project.student,
            report_type="FINAL_REPORT"
        )
        .order_by(
            "-submitted_at"
        )
        .first()
    )

    # -----------------------------------------------------
    # GUIDE EVALUATION
    # -----------------------------------------------------

    evaluation = (
        GuideEvaluation.objects
        .filter(
            project=project
        )
        .first()
    )

    # -----------------------------------------------------
    # WEEKLY REPORT COUNTS
    # -----------------------------------------------------

    weekly_count = weekly_reports.count()

    reviewed_weekly_count = (
        weekly_reports
        .filter(
            status="REVIEWED"
        )
        .count()
    )

    pending_weekly_count = (
        weekly_reports
        .filter(
            status="SUBMITTED"
        )
        .count()
    )

    changes_required_weekly_count = (
        weekly_reports
        .filter(
            status="CHANGES_REQUIRED"
        )
        .count()
    )

    # -----------------------------------------------------
    # ALL WEEKLY REPORTS REVIEWED
    # -----------------------------------------------------

    all_weekly_reviewed = (
        weekly_count > 0
        and reviewed_weekly_count == weekly_count
    )

    # -----------------------------------------------------
    # FINAL REPORT STATUS
    # -----------------------------------------------------

    final_report_reviewed = (
        final_report is not None
        and final_report.status == "REVIEWED"
    )

    final_report_pending = (
        final_report is not None
        and final_report.status == "SUBMITTED"
    )

    final_report_changes_required = (
        final_report is not None
        and final_report.status == "CHANGES_REQUIRED"
    )

    # -----------------------------------------------------
    # CAN ENTER FINAL MARK
    # -----------------------------------------------------

    can_evaluate = (
        final_report is not None
        and final_report_reviewed
        and all_weekly_reviewed
    )

    # -----------------------------------------------------
    # EVALUATION FORM
    # -----------------------------------------------------

    evaluation_form = None

    if can_evaluate:

        if evaluation:
            evaluation_form = GuideEvaluationForm(
                instance=evaluation
            )
        else:
            evaluation_form = GuideEvaluationForm()

    # -----------------------------------------------------
    # RENDER
    # -----------------------------------------------------

    return render(
        request,
        "guide/project_detail.html",
        {
            "project": project,
            "project_messages": project_messages,

            "weekly_reports": weekly_reports,
            "final_report": final_report,

            "weekly_count": weekly_count,
            "reviewed_weekly_count": reviewed_weekly_count,
            "pending_weekly_count": pending_weekly_count,
            "changes_required_weekly_count": (
                changes_required_weekly_count
            ),

            "all_weekly_reviewed": all_weekly_reviewed,

            "final_report_reviewed": final_report_reviewed,
            "final_report_pending": final_report_pending,
            "final_report_changes_required": (
                final_report_changes_required
            ),

            "evaluation": evaluation,
            "evaluation_form": evaluation_form,

            "can_evaluate": can_evaluate,
        }
    )


# =========================================================
# SEND MESSAGE
# =========================================================

@guide_required
def send_message(request, proposal_id):
    if request.method == "POST":
        project = get_object_or_404(ProjectProposal, id=proposal_id, guide=request.user)
        message_text = request.POST.get("message", "").strip()
        if message_text:
            ProjectMessage.objects.create(
                project=project,
                sender=request.user,
                message=message_text
            )
        next_url = request.GET.get('next')
        if next_url:
            return redirect(next_url)
        return redirect("guides:project_detail", proposal_id=project.id)
    return redirect("guides:dashboard")


# =========================================================
# REVIEW PROGRESS REPORT
# =========================================================

@guide_required
def review_progress(request, progress_id):

    # -----------------------------------------------------
    # GET REPORT
    # -----------------------------------------------------

    progress = get_object_or_404(
        ProjectProgress,
        id=progress_id,
        project__guide=request.user
    )

    # -----------------------------------------------------
    # ONLY POST ALLOWED
    # -----------------------------------------------------

    if request.method != "POST":

        return redirect(
            "guides:project_detail",
            proposal_id=progress.project.id
        )

    # -----------------------------------------------------
    # GET STATUS
    # -----------------------------------------------------

    status = request.POST.get(
        "status"
    )

    feedback = request.POST.get(
        "feedback",
        ""
    ).strip()

    # Extract dynamic categories
    criteria_titles = request.POST.getlist('criteria_title[]')
    criteria_marks = request.POST.getlist('criteria_mark[]')
    
    detailed_marks = {}
    total_marks = 0.0
    
    if criteria_titles and criteria_marks and len(criteria_titles) == len(criteria_marks):
        for title, mark in zip(criteria_titles, criteria_marks):
            title = title.strip()
            try:
                mark_val = float(mark)
                if title:
                    detailed_marks[title] = mark_val
                    total_marks += mark_val
            except ValueError:
                pass
                
    if detailed_marks:
        progress.detailed_marks = detailed_marks
        progress.marks = total_marks

    # -----------------------------------------------------
    # VALIDATE STATUS
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
            "guides:report_detail",
            progress_id=progress.id
        )

    # -----------------------------------------------------
    # SAVE REVIEW
    # -----------------------------------------------------

    progress.status = status

    progress.guide_feedback = feedback

    progress.reviewed_at = timezone.now()

    update_fields = [
        "status",
        "guide_feedback",
        "reviewed_at",
    ]
    if detailed_marks:
        update_fields.extend(["marks", "detailed_marks"])

    progress.save(
        update_fields=update_fields
    )

    # -----------------------------------------------------
    # FINAL REPORT
    # -----------------------------------------------------

    if progress.report_type == "FINAL_REPORT":

        if status == "REVIEWED":

            messages.success(
                request,
                "Final report reviewed successfully."
            )

        else:

            messages.warning(
                request,
                "Final report marked as changes required."
            )

    # -----------------------------------------------------
    # WEEKLY REPORT
    # -----------------------------------------------------

    elif progress.report_type in ["PROGRESS_1", "PROGRESS_2", "PROGRESS_3"]:

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

    # -----------------------------------------------------
    # REDIRECT
    # -----------------------------------------------------

    return redirect(
        "guides:report_detail",
        progress_id=progress.id
    )


# =========================================================
# EVALUATE PROJECT
# =========================================================

@guide_required
def evaluate_project(request, proposal_id):

    # -----------------------------------------------------
    # GET PROJECT
    # -----------------------------------------------------

    project = get_object_or_404(
        ProjectProposal,
        id=proposal_id,
        guide=request.user
    )

    # -----------------------------------------------------
    # GET FINAL REPORT
    # -----------------------------------------------------

    final_report = (
        ProjectProgress.objects
        .filter(
            project=project,
            student=project.student,
            report_type="FINAL_REPORT"
        )
        .order_by(
            "-submitted_at"
        )
        .first()
    )

    # -----------------------------------------------------
    # FINAL REPORT REQUIRED
    # -----------------------------------------------------

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
            "Final report must be reviewed before entering the final mark."
        )

        return redirect(
            "guides:project_detail",
            proposal_id=project.id
        )

    # -----------------------------------------------------
    # GET WEEKLY REPORTS
    # -----------------------------------------------------

    weekly_reports = (
        ProjectProgress.objects
        .filter(
            project=project,
            student=project.student,
            report_type__in=["PROGRESS_1", "PROGRESS_2", "PROGRESS_3"]
        )
        .order_by(
            "submitted_at"
        )
    )

    weekly_count = weekly_reports.count()

    reviewed_weekly_count = (
        weekly_reports
        .filter(
            status="REVIEWED"
        )
        .count()
    )

    # -----------------------------------------------------
    # WEEKLY REPORT REQUIRED
    # -----------------------------------------------------

    if weekly_count == 0:

        messages.error(
            request,
            "Student must submit at least one weekly progress report before final evaluation."
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
            "All weekly progress reports must be reviewed before entering the final mark."
        )

        return redirect(
            "guides:project_detail",
            proposal_id=project.id
        )

    # -----------------------------------------------------
    # EXISTING EVALUATION
    # -----------------------------------------------------

    evaluation = (
        GuideEvaluation.objects
        .filter(
            project=project
        )
        .first()
    )

    # -----------------------------------------------------
    # POST
    # -----------------------------------------------------

    if request.method == "POST":

        feedback = request.POST.get("feedback", "").strip()
        titles = request.POST.getlist("criteria_title[]")
        marks = request.POST.getlist("criteria_mark[]")

        if len(titles) != len(marks):
            messages.error(request, "Each mark category must have a matching mark.")
            return redirect("guides:project_detail", proposal_id=project.id)

        detailed_marks = {}
        total_marks = Decimal("0")

        for title_text, mark_text in zip(titles, marks):
            title = title_text.strip()
            mark_text = mark_text.strip()

            if not title and not mark_text:
                continue
            if not title or not mark_text:
                messages.error(
                    request,
                    "Enter both a category name and mark for every row.",
                )
                return redirect("guides:project_detail", proposal_id=project.id)
            if title in detailed_marks:
                messages.error(request, "Mark category names must be unique.")
                return redirect("guides:project_detail", proposal_id=project.id)

            try:
                mark_value = Decimal(mark_text)
            except InvalidOperation:
                messages.error(request, "Enter a valid number for each mark.")
                return redirect("guides:project_detail", proposal_id=project.id)

            if (
                not mark_value.is_finite()
                or mark_value < 0
                or mark_value > 100
                or mark_value.as_tuple().exponent < -2
            ):
                messages.error(
                    request,
                    "Each mark must be between 0 and 100 with at most two decimal places.",
                )
                return redirect("guides:project_detail", proposal_id=project.id)

            detailed_marks[title] = str(mark_value)
            total_marks += mark_value

        if not detailed_marks:
            messages.error(request, "Add at least one mark category.")
            return redirect("guides:project_detail", proposal_id=project.id)

        if total_marks > 100:
            messages.error(request, "Total marks cannot exceed 100.")
            return redirect("guides:project_detail", proposal_id=project.id)

        if not evaluation:
            evaluation = GuideEvaluation(project=project, guide=request.user)
            
        evaluation.feedback = feedback
        evaluation.detailed_marks = detailed_marks
        evaluation.marks = total_marks
        evaluation.save()

        # ---------------------------------------------
        # PROJECT COMPLETED
        # ---------------------------------------------

        project.status = "COMPLETED"

        project.save(
            update_fields=[
                "status"
            ]
        )

        messages.success(
            request,
            "Final mark saved successfully. Project marked as completed."
        )

        return redirect(
            "guides:project_detail",
            proposal_id=project.id
        )

    # -----------------------------------------------------
    # GET
    # -----------------------------------------------------

    else:

        if evaluation:

            form = GuideEvaluationForm(
                instance=evaluation
            )

        else:

            form = GuideEvaluationForm()

    # -----------------------------------------------------
    # RENDER
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # ONLY GUIDE ASSIGNED PROJECT CAN START
    # -----------------------------------------------------

    if project.status != "GUIDE_ASSIGNED":

        messages.error(
            request,
            "This project cannot be started."
        )

        return redirect(
            "guides:project_detail",
            proposal_id=project.id
        )

    # -----------------------------------------------------
    # START
    # -----------------------------------------------------

    project.status = "IN_PROGRESS"

    project.save(
        update_fields=[
            "status"
        ]
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

    # -----------------------------------------------------
    # ONLY GUIDE ASSIGNED PROJECT CAN BE REJECTED
    # -----------------------------------------------------

    if project.status != "GUIDE_ASSIGNED":

        messages.error(
            request,
            "This project cannot be rejected at this stage."
        )

        return redirect(
            "guides:project_detail",
            proposal_id=project.id
        )

    # -----------------------------------------------------
    # POST ONLY
    # -----------------------------------------------------

    if request.method == "POST":

        reason = request.POST.get(
            "guide_rejection_reason",
            ""
        ).strip()

        # ---------------------------------------------
        # REASON REQUIRED
        # ---------------------------------------------

        if not reason:

            messages.error(
                request,
                "Please enter a rejection reason."
            )

            return redirect(
                "guides:project_detail",
                proposal_id=project.id
            )

        # ---------------------------------------------
        # SAVE REJECTION
        # ---------------------------------------------

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

    # -----------------------------------------------------
    # REDIRECT
    # -----------------------------------------------------

    return redirect(
        "guides:students"
    )

@login_required
@guide_required
def student_reports(request, proposal_id):
    project = get_object_or_404(ProjectProposal, id=proposal_id, guide=request.user)
    reports = ProjectProgress.objects.filter(project=project).order_by('-submitted_at')
    project_messages = project.messages.select_related("sender").all()
    
    return render(request, 'guide/student_reports_list.html', {
        'project': project,
        'reports': reports,
        'project_messages': project_messages
    })

@login_required
@guide_required
def report_detail(request, progress_id):
    report = get_object_or_404(
        ProjectProgress.objects.select_related('project', 'project__student'), 
        id=progress_id, 
        project__guide=request.user
    )
    
    return render(request, 'guide/report_detail.html', {
        'report': report,
        'project': report.project
    })
