from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)

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

    assigned_count = assigned_projects.count()

    guide_rejected_count = assigned_projects.filter(
        status="GUIDE_REJECTED"
    ).count()

    in_progress_count = assigned_projects.filter(
        status="IN_PROGRESS"
    ).count()

    completed_count = assigned_projects.filter(
        status="COMPLETED"
    ).count()

    return render(
        request,
        "guides/dashboard.html",
        {
            "assigned_projects": assigned_projects,
            "assigned_count": assigned_count,
            "guide_rejected_count": guide_rejected_count,
            "in_progress_count": in_progress_count,
            "completed_count": completed_count,
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
        "guides/students.html",
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

    # Get weekly progress reports
    progress_reports = (
        ProjectProgress.objects
        .filter(
            project=proposal,
            student=proposal.student,
        )
        .order_by(
            "-week_number",
            "-submitted_at",
        )
    )

    # Get existing evaluation
    evaluation = (
        GuideEvaluation.objects
        .filter(
            project=proposal,
            guide=request.user,
        )
        .first()
    )

    if evaluation:
        evaluation_form = GuideEvaluationForm(
            instance=evaluation
        )
    else:
        evaluation_form = GuideEvaluationForm()

    return render(
        request,
        "guide/project_detail.html",
        {
            "proposal": proposal,
            "project": proposal,
            "progress_reports": progress_reports,
            "evaluation": evaluation,
            "evaluation_form": evaluation_form,
        }
    )


# =========================================================
# GUIDE EVALUATION / MARKS
# =========================================================

@guide_required
def evaluate_project(request, proposal_id):

    proposal = get_object_or_404(
        ProjectProposal,
        id=proposal_id,
        guide=request.user,
    )

    # Only POST is allowed
    if request.method != "POST":

        return redirect(
            "guides:project_detail",
            proposal_id=proposal.id,
        )

    evaluation = (
        GuideEvaluation.objects
        .filter(
            project=proposal,
            guide=request.user,
        )
        .first()
    )

    if evaluation:

        form = GuideEvaluationForm(
            request.POST,
            instance=evaluation,
        )

    else:

        form = GuideEvaluationForm(
            request.POST
        )

    if form.is_valid():

        evaluation = form.save(
            commit=False
        )

        evaluation.project = proposal
        evaluation.guide = request.user

        evaluation.save()

        messages.success(
            request,
            "Student evaluation and marks have been saved successfully."
        )

        return redirect(
            "guides:project_detail",
            proposal_id=proposal.id,
        )

    # If validation fails, show the same page
    progress_reports = (
        ProjectProgress.objects
        .filter(
            project=proposal,
            student=proposal.student,
        )
        .order_by(
            "-week_number",
            "-submitted_at",
        )
    )

    return render(
        request,
        "guides/project_detail.html",
        {
            "proposal": proposal,
            "project": proposal,
            "progress_reports": progress_reports,
            "evaluation": evaluation,
            "evaluation_form": form,
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

    # Only POST
    if request.method != "POST":

        return redirect(
            "guides:project_detail",
            proposal_id=proposal.id,
        )

    # Guide can reject only assigned projects
    if proposal.status != "GUIDE_ASSIGNED":

        messages.error(
            request,
            "This project cannot be rejected at its current stage."
        )

        return redirect(
            "guides:project_detail",
            proposal_id=proposal.id,
        )

    proposal.status = "GUIDE_REJECTED"

    proposal.save(
        update_fields=[
            "status",
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

    if request.method != "POST":

        return redirect(
            "guides:project_detail",
            proposal_id=proposal.id,
        )

    if proposal.status != "GUIDE_ASSIGNED":

        messages.error(
            request,
            "This project cannot be started at the current stage."
        )

        return redirect(
            "guides:project_detail",
            proposal_id=proposal.id,
        )

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