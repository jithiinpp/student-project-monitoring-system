from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ProjectProposalForm
from .models import ProjectProposal


@login_required
def student_proposals(request):

    if request.user.is_superuser:
        return redirect("coordinator_dashboard")

    if request.user.role != "STUDENT":
        return redirect("dashboard")

    proposals = ProjectProposal.objects.filter(
        student=request.user
    ).order_by("-created_at")

    proposal_count = proposals.count()

    return render(
        request,
        "student/proposals.html",
        {
            "proposals": proposals,
            "proposal_count": proposal_count,
        }
    )


@login_required
def add_proposal(request):

    # Only students can submit proposals
    if request.user.is_superuser:
        return redirect("coordinator_dashboard")

    if request.user.role != "STUDENT":
        return redirect("dashboard")

    # Count student's existing proposals
    proposal_count = ProjectProposal.objects.filter(
        student=request.user
    ).count()

    # Maximum 3 proposals
    if proposal_count >= 3:
        messages.error(
            request,
            "You have already submitted the maximum of 3 proposals."
        )
        return redirect("student_proposals")

    # -------------------------
    # SUBMIT PROPOSAL
    # -------------------------
    if request.method == "POST":

        form = ProjectProposalForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            # Don't save yet because student
            # must be attached to the proposal
            proposal = form.save(commit=False)

            # Assign logged-in student
            proposal.student = request.user

            # Initial status
            proposal.status = "SUBMITTED"

            # Save proposal
            proposal.save()

            messages.success(
                request,
                "Your project proposal has been submitted successfully."
            )

            # Go to proposal list
            return redirect("student_proposals")

    else:
        # Display empty form
        form = ProjectProposalForm()

    return render(
        request,
        "student/proposal_form.html",
        {
            "form": form,
            "proposal_count": proposal_count,
        }
    )


@login_required
def proposal_detail(request, proposal_id):

    if request.user.is_superuser:
        return redirect("coordinator_dashboard")

    if request.user.role != "STUDENT":
        return redirect("dashboard")

    proposal = get_object_or_404(
        ProjectProposal,
        id=proposal_id,
        student=request.user
    )

    return render(
        request,
        "student/proposal_detail.html",
        {
            "proposal": proposal
        }
    )