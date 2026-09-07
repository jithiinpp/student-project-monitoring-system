from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import StudentRegistrationForm
from .models import User


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

            # Every user registering through this form is a student
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

    # Superuser → Coordinator dashboard
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

    return render(
        request,
        "student/dashboard.html"
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

    # IMPORTANT:
    # This temporarily works even if the Proposal model
    # has not been created yet.

    context = {
        "proposals": [],
        "proposal_count": 0,
    }

    return render(
        request,
        "student/proposals.html",
        context
    )


# ============================================================
# ADD PROPOSAL
# ============================================================

@login_required
def add_proposal(request):

    # Superuser → Coordinator
    if request.user.is_superuser:
        return redirect("accounts:coordinator_dashboard")

    # Only students
    if request.user.role != "STUDENT":
        return redirect("accounts:dashboard")

    # Temporary proposal count
    proposal_count = 0

    if proposal_count >= 3:

        messages.warning(
            request,
            "You have already submitted the maximum of 3 proposals."
        )

        return redirect("accounts:student_proposals")

    return render(
        request,
        "student/add_proposal.html",
        {
            "proposal_count": proposal_count,
        }
    )


# ============================================================
# PROPOSAL DETAIL
# ============================================================

@login_required
def proposal_detail(request, proposal_id):

    # Superuser → Coordinator
    if request.user.is_superuser:
        return redirect("accounts:coordinator_dashboard")

    # Only students
    if request.user.role != "STUDENT":
        return redirect("accounts:dashboard")

    # --------------------------------------------------------
    # IMPORTANT
    # --------------------------------------------------------
    # This requires a Proposal model in your projects app.
    #
    # If you have not created Proposal model yet, do not
    # visit this page until the project/proposal app is ready.
    # --------------------------------------------------------

    try:

        from projects.models import Proposal

    except ImportError:

        messages.error(
            request,
            "Proposal system is not configured yet."
        )

        return redirect("accounts:student_proposals")

    proposal = get_object_or_404(
        Proposal,
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

    # Superuser is allowed
    if not request.user.is_superuser:

        if request.user.role != "COORDINATOR":
            return redirect("accounts:dashboard")

    students = User.objects.filter(
        role="STUDENT"
    ).order_by("-date_joined")

    context = {
        "students": students,
        "student_count": students.count(),
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

    return render(
        request,
        "expert/dashboard.html"
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