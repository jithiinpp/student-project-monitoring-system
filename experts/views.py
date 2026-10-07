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

        # Superuser can access Expert pages
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)

        # Only Domain Expert
        if not request.user.is_expert:

            messages.error(
                request,
                "You are not authorized to access the Expert page."
            )

            return redirect("accounts:dashboard")

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
        .select_related(
            "student",
            "domain_expert"
        )
        .order_by("submitted_at")
    )

    total_proposals = proposals.count()

    assigned_count = proposals.filter(
        status="EXPERT_ASSIGNED"
    ).count()

    approved_count = proposals.filter(
        status__in=[
            "EXPERT_APPROVED",
            "COORDINATOR_APPROVED",
            "GUIDE_ASSIGNED",
            "GUIDE_REJECTED",
            "IN_PROGRESS",
            "COMPLETED"
        ]
    ).count()

    changes_count = proposals.filter(
        status__in=["CHANGES_REQUESTED", "CHANGES_SENT_TO_STUDENT"]
    ).count()

    submitted_count = proposals.filter(
        status="SUBMITTED"
    ).count()

    context = {
        "proposals": proposals,

        "total_proposals": total_proposals,

        "assigned_count": assigned_count,

        "approved_count": approved_count,

        "changes_count": changes_count,

        "submitted_count": submitted_count,
        
        "scheduled_reviews": proposals.exclude(review_date__isnull=True).order_by("review_date"),
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
        .select_related(
            "student",
            "domain_expert"
        )
        .order_by("submitted_at")
    )

    status_filter = request.GET.get('status')
    if status_filter:
        if status_filter == "EXPERT_APPROVED":
            proposals = proposals.filter(
                status__in=[
                    "EXPERT_APPROVED",
                    "COORDINATOR_APPROVED",
                    "GUIDE_ASSIGNED",
                    "GUIDE_REJECTED",
                    "IN_PROGRESS",
                    "COMPLETED"
                ]
            )
        elif status_filter == "CHANGES_REQUESTED":
            proposals = proposals.filter(
                status__in=["CHANGES_REQUESTED", "CHANGES_SENT_TO_STUDENT"]
            )
        else:
            proposals = proposals.filter(status=status_filter)

    # Note: assigned_count is calculated BEFORE filtering, so we need a base query
    base_proposals = ProjectProposal.objects.filter(domain_expert=request.user)
    assigned_count = base_proposals.filter(
        status="EXPERT_ASSIGNED"
    ).count()

    return render(
        request,
        "experts/proposals.html",
        {
            "proposals": proposals,
            "assigned_count": assigned_count
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

    change_requests = (
        ProposalChangeRequest.objects
        .filter(
            proposal=proposal
        )
        .select_related(
            "expert",
            "coordinator"
        )
        .order_by("-created_at")
    )

    project_messages = proposal.messages.select_related("sender").all()

    return render(
        request,
        "experts/proposal_detail.html",
        {
            "proposal": proposal,
            "change_requests": change_requests,
            "project_messages": project_messages,
        }
    )

# =========================================================
# EXPERT SEND MESSAGE
# =========================================================

@expert_required
def expert_send_message(request, proposal_id):
    if request.method == "POST":
        proposal = get_object_or_404(ProjectProposal, id=proposal_id, domain_expert=request.user)
        message_text = request.POST.get("message", "").strip()
        if message_text:
            from projects.models import ProjectMessage
            ProjectMessage.objects.create(
                project=proposal,
                sender=request.user,
                message=message_text
            )
        referer = request.META.get('HTTP_REFERER')
        if referer:
            return redirect(referer)
    return redirect("experts:proposal_detail", proposal_id=proposal_id)


# =========================================================
# REVIEW PROPOSAL
# =========================================================
#
# Expert has ONLY two decisions:
#
# 1. APPROVE
#       EXPERT_APPROVED
#       ↓
#       Coordinator
#       ↓
#       Final approval
#
# 2. REQUEST CHANGES
#       PENDING
#       ↓
#       Coordinator
#       ↓
#       Student
#
# Expert does NOT give final approval.
# =========================================================

@expert_required
def review_proposal(request, proposal_id):

    proposal = get_object_or_404(
        ProjectProposal,
        id=proposal_id,
        domain_expert=request.user
    )

    # -----------------------------------------------------
    # ONLY POST REQUEST ALLOWED
    # -----------------------------------------------------

    if request.method != "POST":

        return redirect(
            "experts:proposal_detail",
            proposal_id=proposal.id
        )

    # -----------------------------------------------------
    # EXPERT CAN REVIEW ONLY ASSIGNED PROPOSALS
    # -----------------------------------------------------

    if proposal.status != "EXPERT_ASSIGNED":

        messages.error(
            request,
            "This proposal is not currently waiting for Expert review."
        )

        return redirect(
            "experts:proposal_detail",
            proposal_id=proposal.id
        )

    decision = request.POST.get(
        "decision",
        ""
    ).strip()

    comments = request.POST.get(
        "comments",
        ""
    ).strip()

    # =====================================================
    # EXPERT APPROVES
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
            "Proposal approved by Expert and sent to Coordinator "
            "for final approval."
        )

        return redirect(
            "experts:my_proposals"
        )

    # =====================================================
    # EXPERT REQUESTS CHANGES
    # =====================================================

    if decision == "changes":

        if not comments:

            messages.error(
                request,
                "Please enter comments explaining the required changes."
            )

            return redirect(
                "experts:proposal_detail",
                proposal_id=proposal.id
            )

        # -------------------------------------------------
        # CREATE CHANGE REQUEST
        # -------------------------------------------------

        ProposalChangeRequest.objects.create(
            proposal=proposal,
            expert=request.user,
            comments=comments,
            status="PENDING"
        )

        # -------------------------------------------------
        # CHANGE PROPOSAL STATUS
        #
        # Coordinator will receive this request.
        # Coordinator must send it to Student.
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
            "Change request sent to Coordinator."
        )

        return redirect(
            "experts:my_proposals"
        )

    # =====================================================
    # INVALID DECISION
    # =====================================================

    messages.error(
        request,
        "Invalid review decision."
    )

    return redirect(
        "experts:proposal_detail",
        proposal_id=proposal.id
    )

@expert_required
def students(request):
    """
    List all students assigned to this domain expert.
    """
    proposals = (
        ProjectProposal.objects
        .filter(domain_expert=request.user)
        .select_related("student")
        .order_by("-updated_at")
    )
    
    # Extract unique students from the proposals
    # Since each student only has one proposal in SPMS typically, we can just pass the proposals, 
    # but let's pass the proposals so we have project details too.
    
    return render(
        request,
        "experts/students.html",
        {"proposals": proposals}
    )