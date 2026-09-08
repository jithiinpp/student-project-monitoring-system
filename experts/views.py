from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from projects.models import ProjectProposal


def expert_required(view_func):

    def wrapper(request, *args, **kwargs):

        if not request.user.is_authenticated:
            return redirect("login")

        if (
            not request.user.is_superuser
            and request.user.role != "EXPERT"
        ):
            messages.error(
                request,
                "You are not authorized to access the Expert page."
            )

            return redirect("dashboard")

        return view_func(request, *args, **kwargs)

    return wrapper


@login_required
@expert_required
def dashboard(request):

    proposals = ProjectProposal.objects.filter(
        domain_expert=request.user
    )

    context = {
        "total_proposals": proposals.count(),

        "assigned_count": proposals.filter(
            status="EXPERT_ASSIGNED"
        ).count(),

        "approved_count": proposals.filter(
            status="EXPERT_APPROVED"
        ).count(),

        "changes_count": proposals.filter(
            status="CHANGES_REQUESTED"
        ).count(),
    }

    return render(
        request,
        "experts/dashboard.html",
        context
    )


@login_required
@expert_required
def my_proposals(request):

    proposals = ProjectProposal.objects.filter(
        domain_expert=request.user
    ).select_related(
        "student"
    )

    return render(
        request,
        "experts/proposals.html",
        {
            "proposals": proposals
        }
    )


@login_required
@expert_required
def proposal_detail(request, proposal_id):

    proposal = get_object_or_404(
        ProjectProposal.objects.select_related(
            "student",
            "domain_expert"
        ),
        id=proposal_id,
        domain_expert=request.user
    )

    return render(
        request,
        "experts/proposal_detail.html",
        {
            "proposal": proposal
        }
    )


@login_required
@expert_required
def review_proposal(request, proposal_id):

    proposal = get_object_or_404(
        ProjectProposal,
        id=proposal_id,
        domain_expert=request.user
    )

    if request.method != "POST":
        return redirect(
            "experts:proposal_detail",
            proposal_id=proposal.id
        )

    decision = request.POST.get("decision")
    comments = request.POST.get("comments", "").strip()

    if decision == "approve":

        proposal.status = "EXPERT_APPROVED"

        proposal.expert_comments = comments

        proposal.save()

        messages.success(
            request,
            "Proposal approved successfully and sent back to Coordinator."
        )

    elif decision == "changes":

        if not comments:
            messages.error(
                request,
                "Please enter comments when requesting changes."
            )

            return redirect(
                "experts:proposal_detail",
                proposal_id=proposal.id
            )

        proposal.status = "CHANGES_REQUESTED"

        proposal.expert_comments = comments

        proposal.save()

        messages.success(
            request,
            "Changes requested. Proposal has been returned to Coordinator."
        )

    else:

        messages.error(
            request,
            "Invalid review decision."
        )

    return redirect(
        "experts:my_proposals"
    )