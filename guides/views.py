from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)

from projects.models import ProjectProposal


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
        .select_related("student")
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
# GUIDE PROJECT DETAIL
# =========================================================

@guide_required
def project_detail(request, proposal_id):

    proposal = get_object_or_404(
        ProjectProposal.objects.select_related(
            "student",
            "domain_expert",
            "guide"
        ),
        id=proposal_id,
        guide=request.user
    )

    return render(
        request,
        "guides/project_detail.html",
        {
            "proposal": proposal
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
        guide=request.user
    )

    # Only POST
    if request.method != "POST":

        return redirect(
            "guides:project_detail",
            proposal_id=proposal.id
        )

    # Guide can reject only assigned projects
    if proposal.status != "GUIDE_ASSIGNED":

        messages.error(
            request,
            "This project cannot be rejected at its current stage."
        )

        return redirect(
            "guides:project_detail",
            proposal_id=proposal.id
        )

    proposal.status = "GUIDE_REJECTED"

    proposal.save(
        update_fields=[
            "status",
            "updated_at"
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
        guide=request.user
    )

    if request.method != "POST":

        return redirect(
            "guides:project_detail",
            proposal_id=proposal.id
        )

    if proposal.status != "GUIDE_ASSIGNED":

        messages.error(
            request,
            "This project cannot be started at the current stage."
        )

        return redirect(
            "guides:project_detail",
            proposal_id=proposal.id
        )

    proposal.status = "IN_PROGRESS"

    proposal.save(
        update_fields=[
            "status",
            "updated_at"
        ]
    )

    messages.success(
        request,
        "Project has been accepted and moved to In Progress."
    )

    return redirect(
        "guides:project_detail",
        proposal_id=proposal.id
    )