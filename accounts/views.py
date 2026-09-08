from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import StudentRegistrationForm
from .models import User

# ProjectProposal is in projects app
from projects.forms import ProjectProposalForm
from projects.models import ProjectProposal


# ============================================================
# LOGIN
# ============================================================

def login_view(request):

    if request.user.is_authenticated:
        return redirect("accounts:dashboard")

    if request.method == "POST":

        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            if not user.is_active:
                messages.error(
                    request,
                    "Your account is inactive."
                )
                return redirect("accounts:login")

            login(request, user)

            return redirect("accounts:dashboard")

        messages.error(
            request,
            "Invalid username or password."
        )

    return render(
        request,
        "accounts/login.html"
    )


# ============================================================
# STUDENT REGISTRATION
# ============================================================

def register_view(request):

    if request.user.is_authenticated:
        return redirect("accounts:dashboard")

    if request.method == "POST":

        form = StudentRegistrationForm(request.POST)

        if form.is_valid():

            user = form.save()

            # All users registering through this form are students
            user.role = "STUDENT"

            user.save(update_fields=["role"])

            messages.success(
                request,
                "Student account created successfully. You can now login."
            )

            return redirect("accounts:login")

    else:

        form = StudentRegistrationForm()

    return render(
        request,
        "accounts/register.html",
        {
            "form": form
        }
    )


# ============================================================
# LOGOUT
# ============================================================

@login_required
def logout_view(request):

    logout(request)

    messages.success(
        request,
        "You have been logged out successfully."
    )

    return redirect("accounts:login")


# ============================================================
# MAIN DASHBOARD REDIRECT
# ============================================================

@login_required
def dashboard_view(request):

    user = request.user

    # Superuser → Coordinator
    if user.is_superuser:
        return redirect("accounts:coordinator_dashboard")

    # Coordinator
    if user.role == "COORDINATOR":
        return redirect("accounts:coordinator_dashboard")

    # Student
    if user.role == "STUDENT":
        return redirect("accounts:student_dashboard")

    # Domain Expert
    if user.role == "EXPERT":
        return redirect("accounts:expert_dashboard")

    # Guide
    if user.role == "GUIDE":
        return redirect("accounts:guide_dashboard")

    # Panel Member
    if user.role == "PANEL":
        return redirect("accounts:panel_dashboard")

    messages.error(
        request,
        "Your account does not have a valid SPMS role."
    )

    logout(request)

    return redirect("accounts:login")


# ============================================================
# STUDENT DASHBOARD
# ============================================================

@login_required
def student_dashboard(request):

    # Superuser → Coordinator
    if request.user.is_superuser:
        return redirect("accounts:coordinator_dashboard")

    # Only students
    if request.user.role != "STUDENT":
        return redirect("accounts:dashboard")

    proposals = (
        ProjectProposal.objects
        .filter(student=request.user)
        .order_by("-id")
    )

    proposal_count = proposals.count()

    context = {
        "proposals": proposals,
        "proposal_count": proposal_count,
    }

    return render(
        request,
        "student/dashboard.html",
        context
    )


# ============================================================
# STUDENT PROPOSALS
# ============================================================

@login_required
def student_proposals(request):

    # Superuser → Coordinator
    if request.user.is_superuser:
        return redirect("accounts:coordinator_dashboard")

    # Only students
    if request.user.role != "STUDENT":
        return redirect("accounts:dashboard")

    proposals = (
        ProjectProposal.objects
        .filter(student=request.user)
        .order_by("-id")
    )

    proposal_count = proposals.count()

    context = {
        "proposals": proposals,
        "proposal_count": proposal_count,
    }

    return render(
        request,
        "student/proposals.html",
        context
    )


# ============================================================
# ADD PROJECT PROPOSAL
# ============================================================

@login_required
def add_proposal(request):

    # Only students can submit proposals
    if request.user.role != "STUDENT":
        return redirect("accounts:dashboard")

    # Count student's proposals
    proposal_count = (
        ProjectProposal.objects
        .filter(student=request.user)
        .count()
    )

    # Maximum 3 proposals
    if proposal_count >= 3:

        messages.error(
            request,
            "You have already submitted the maximum of 3 proposals."
        )

        return redirect(
            "accounts:student_proposals"
        )

    # ========================================================
    # POST
    # ========================================================

    if request.method == "POST":

        form = ProjectProposalForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            proposal = form.save(commit=False)

            # Automatically assign current student
            proposal.student = request.user

            # Initial status
            proposal.status = "SUBMITTED"

            proposal.save()

            messages.success(
                request,
                "Project proposal submitted successfully."
            )

            return redirect(
                "accounts:student_proposals"
            )

        else:

            messages.error(
                request,
                "Please correct the errors in the form."
            )

            print("====================================")
            print("PROPOSAL FORM ERRORS:")
            print(form.errors)
            print("====================================")

    # ========================================================
    # GET
    # ========================================================

    else:

        form = ProjectProposalForm()

    return render(
        request,
        "student/proposal_form.html",
        {
            "form": form,
            "proposal_count": proposal_count,
        }
    )


# ============================================================
# STUDENT PROPOSAL DETAIL
# ============================================================

@login_required
def proposal_detail(request, proposal_id):

    # Superuser → Coordinator
    if request.user.is_superuser:
        return redirect("accounts:coordinator_dashboard")

    # Only students
    if request.user.role != "STUDENT":
        return redirect("accounts:dashboard")

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


# ============================================================
# COORDINATOR DASHBOARD
# ============================================================

@login_required
def coordinator_dashboard(request):

    # Superuser allowed
    if not request.user.is_superuser:

        if request.user.role != "COORDINATOR":
            return redirect("accounts:dashboard")

    # Students
    students = (
        User.objects
        .filter(role="STUDENT")
        .order_by("-date_joined")
    )

    # All project proposals
    proposals = (
        ProjectProposal.objects
        .select_related("student", "domain_expert")
        .order_by("-submitted_at")
    )

    context = {
        "students": students,
        "student_count": students.count(),

        "proposals": proposals,
        "proposal_count": proposals.count(),

        # Proposal status counts
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


# ============================================================
# EXPERT DASHBOARD
# ============================================================

@login_required
def expert_dashboard(request):

    if request.user.is_superuser:
        return redirect("accounts:coordinator_dashboard")

    if request.user.role != "EXPERT":
        return redirect("accounts:dashboard")

    # Proposals assigned to this expert
    proposals = (
        ProjectProposal.objects
        .filter(domain_expert=request.user)
        .select_related("student")
        .order_by("-submitted_at")
    )

    context = {
        "proposals": proposals,
        "proposal_count": proposals.count(),
    }

    return render(
        request,
        "expert/dashboard.html",
        context
    )


# ============================================================
# GUIDE DASHBOARD
# ============================================================

@login_required
def guide_dashboard(request):

    if request.user.is_superuser:
        return redirect("accounts:coordinator_dashboard")

    if request.user.role != "GUIDE":
        return redirect("accounts:dashboard")

    return render(
        request,
        "guide/dashboard.html"
    )


# ============================================================
# PANEL DASHBOARD
# ============================================================

@login_required
def panel_dashboard(request):

    if request.user.is_superuser:
        return redirect("accounts:coordinator_dashboard")

    if request.user.role != "PANEL":
        return redirect("accounts:dashboard")

    return render(
        request,
        "panel/dashboard.html"
    )