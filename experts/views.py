from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from projects.models import (
    ProjectProposal,
    ProposalChangeRequest,
)


# =========================================================
# EXPERT ACCESS CHECK
# =========================================================

def expert_required(view_func):

    @login_required
    def wrapper(request, *args, **kwargs):

        # Superuser can access Expert page
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)

        # Only Expert
        if request.user.role != "EXPERT":

            messages.error(
                request,
                "You are not authorized to access the Expert page."
            )

            return redirect(
                "accounts:dashboard"
            )

        return view_func(request, *args, **kwargs)

    return wrapper


# =========================================================
# EXPERT DASHBOARD
# =========================================================

@expert_required
def dashboard(request):

    proposals = (
        ProjectProposal.objects
        .filter(
            domain_expert=request.user
        )
        .select_related("student")
    )

    total_proposals = proposals.count()

    assigned_count = proposals.filter(
        status="EXPERT_ASSIGNED"
    ).count()

    approved_count = proposals.filter(
        status="EXPERT_APPROVED"
    ).count()

    changes_count = proposals.filter(
        status="CHANGES_REQUESTED"
    ).count()

    submitted_count = proposals.filter(
        status="SUBMITTED"
    ).count()

    context = {

        "total_proposals": total_proposals,

        "assigned_count": assigned_count,

        "approved_count": approved_count,

        "changes_count": changes_count,

        "submitted_count": submitted_count,

        "proposals": proposals.order_by(
            "-updated_at"
        ),
    }

    return render(
        request,
        "experts/dashboard.html",
        context
    )


# =========================================================
# MY ASSIGNED PROPOSALS
# =========================================================

@expert_required
def my_proposals(request):

    proposals = (
        ProjectProposal.objects
        .filter(
            domain_expert=request.user
        )
        .select_related("student")
        .order_by("-updated_at")
    )

    return render(
        request,
        "experts/proposals.html",
        {
            "proposals": proposals
        }
    )


# =========================================================
# PROPOSAL DETAIL
# =========================================================

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


# =========================================================
# REVIEW PROPOSAL
# =========================================================

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

    decision = request.POST.get(
        "decision"
    )

    comments = request.POST.get(
        "comments",
        ""
    ).strip()


    # =====================================================
    # APPROVE
    # =====================================================

    if decision == "approve":

        proposal.status = "EXPERT_APPROVED"

        proposal.expert_comments = comments

        proposal.save(
            update_fields=[
                "status",
                "expert_comments",
                "updated_at"
            ]
        )

        messages.success(
            request,
            "Proposal approved successfully and sent back to Coordinator."
        )


    # =====================================================
    # REQUEST CHANGES
    # =====================================================

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

        # -------------------------------------------------
        # Create Change Request
        # -------------------------------------------------

        ProposalChangeRequest.objects.create(

            proposal=proposal,

            expert=request.user,

            message=comments,

            status="PENDING"
        )

        # -------------------------------------------------
        # Change proposal status
        # -------------------------------------------------

        proposal.status = "CHANGES_REQUESTED"

        proposal.expert_comments = comments

        proposal.save(
            update_fields=[
                "status",
                "expert_comments",
                "updated_at"
            ]
        )

        messages.success(
            request,
            "Changes requested. The request has been sent to the Coordinator for review."
        )


    # =====================================================
    # INVALID DECISION
    # =====================================================

    else:

        messages.error(
            request,
            "Invalid review decision."
        )


    return redirect(
        "experts:my_proposals"
    )