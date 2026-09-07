from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import User
from projects.models import ProjectProposal


def coordinator_required(view_func):

    def wrapper(request, *args, **kwargs):

        if not request.user.is_authenticated:
            return redirect("login")

        if (
            not request.user.is_superuser
            and request.user.role != "COORDINATOR"
        ):
            messages.error(
                request,
                "You are not authorized to access the Coordinator page."
            )

            return redirect("dashboard")

        return view_func(request, *args, **kwargs)

    return wrapper


@login_required
@coordinator_required
def dashboard(request):

    students = User.objects.filter(
        role="STUDENT"
    )

    experts = User.objects.filter(
        role="EXPERT"
    )

    guides = User.objects.filter(
        role="GUIDE"
    )

    panels = User.objects.filter(
        role="PANEL"
    )

    proposals = ProjectProposal.objects.all()

    context = {

        "student_count": students.count(),

        "expert_count": experts.count(),

        "guide_count": guides.count(),

        "panel_count": panels.count(),

        "proposal_count": proposals.count(),

        "submitted_count": proposals.filter(
            status="SUBMITTED"
        ).count(),

        "expert_assigned_count": proposals.filter(
            status="EXPERT_ASSIGNED"
        ).count(),

        "expert_approved_count": proposals.filter(
            status="EXPERT_APPROVED"
        ).count(),

        "approved_count": proposals.filter(
            status="COORDINATOR_APPROVED"
        ).count(),
    }

    return render(
        request,
        "coordinator/dashboard.html",
        context
    )


@login_required
@coordinator_required
def proposals(request):

    proposals = ProjectProposal.objects.select_related(
        "student"
    ).all()

    return render(
        request,
        "coordinator/proposals.html",
        {
            "proposals": proposals
        }
    )


@login_required
@coordinator_required
def proposal_detail(request, proposal_id):

    proposal = get_object_or_404(
        ProjectProposal.objects.select_related(
            "student"
        ),
        id=proposal_id
    )

    experts = User.objects.filter(
        role="EXPERT",
        is_active=True
    ).order_by(
        "first_name",
        "username"
    )

    return render(
        request,
        "coordinator/proposal_detail.html",
        {
            "proposal": proposal,
            "experts": experts,
        }
    )


@login_required
@coordinator_required
def assign_expert(request, proposal_id):

    proposal = get_object_or_404(
        ProjectProposal,
        id=proposal_id
    )

    if request.method != "POST":

        return redirect(
            "coordinator:proposal_detail",
            proposal_id=proposal.id
        )

    expert_id = request.POST.get(
        "expert"
    )

    if not expert_id:

        messages.error(
            request,
            "Please select a Domain Expert."
        )

        return redirect(
            "coordinator:proposal_detail",
            proposal_id=proposal.id
        )

    expert = get_object_or_404(
        User,
        id=expert_id,
        role="EXPERT",
        is_active=True
    )

    proposal.domain_expert = expert

    proposal.status = "EXPERT_ASSIGNED"

    proposal.save(
        update_fields=[
            "domain_expert",
            "status",
            "updated_at",
        ]
    )

    messages.success(
        request,
        f"Domain Expert {expert.get_full_name() or expert.username} "
        f"has been assigned successfully."
    )

    return redirect(
        "coordinator:proposal_detail",
        proposal_id=proposal.id
    )