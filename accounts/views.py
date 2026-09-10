from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import StudentRegistrationForm
from .models import User

from projects.forms import (
    ProjectProposalForm,
    ProjectProgressForm,
)

from projects.models import (
    ProjectProposal,
    ProjectProgress,
)


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

            # All registrations from this form are students
            user.role = "STUDENT"

            user.save(
                update_fields=["role"]
            )

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

    # --------------------------------------------------------
    # SUPERUSER → COORDINATOR
    # --------------------------------------------------------

    if user.is_superuser:

        return redirect(
            "accounts:coordinator_dashboard"
        )

    # --------------------------------------------------------
    # COORDINATOR
    # --------------------------------------------------------

    if user.role == "COORDINATOR":

        return redirect(
            "accounts:coordinator_dashboard"
        )

    # --------------------------------------------------------
    # STUDENT
    # --------------------------------------------------------

    if user.role == "STUDENT":

        return redirect(
            "accounts:student_dashboard"
        )

    # --------------------------------------------------------
    # DOMAIN EXPERT
    # --------------------------------------------------------

    if user.role == "EXPERT":

        return redirect(
            "accounts:expert_dashboard"
        )

    # --------------------------------------------------------
    # GUIDE
    # --------------------------------------------------------

    if user.role == "GUIDE":

        return redirect(
            "accounts:guide_dashboard"
        )

    # --------------------------------------------------------
    # PANEL MEMBER
    # --------------------------------------------------------

    if user.role == "PANEL":

        return redirect(
            "accounts:panel_dashboard"
        )

    # --------------------------------------------------------
    # INVALID ROLE
    # --------------------------------------------------------

    messages.error(
        request,
        "Your account does not have a valid SPMS role."
    )

    logout(request)

    return redirect(
        "accounts:login"
    )


# ============================================================
# STUDENT DASHBOARD
# ============================================================

@login_required
def student_dashboard(request):

    # Superuser → Coordinator
    if request.user.is_superuser:

        return redirect(
            "accounts:coordinator_dashboard"
        )

    # Only students
    if request.user.role != "STUDENT":

        return redirect(
            "accounts:dashboard"
        )

    proposals = (
        ProjectProposal.objects
        .filter(
            student=request.user
        )
        .order_by("-id")
    )

    proposal_count = proposals.count()

    # --------------------------------------------------------
    # UNDER REVIEW
    # --------------------------------------------------------

    pending_count = proposals.filter(
        status__in=[
            "SUBMITTED",
            "EXPERT_ASSIGNED",
            "CHANGES_REQUESTED",
        ]
    ).count()

    # --------------------------------------------------------
    # APPROVED / ACTIVE
    # --------------------------------------------------------

    approved_count = proposals.filter(
        status__in=[
            "EXPERT_APPROVED",
            "COORDINATOR_APPROVED",
            "GUIDE_ASSIGNED",
            "IN_PROGRESS",
            "COMPLETED",
        ]
    ).count()

    context = {
        "proposals": proposals,
        "proposal_count": proposal_count,
        "pending_count": pending_count,
        "approved_count": approved_count,
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

        return redirect(
            "accounts:coordinator_dashboard"
        )

    # Only students
    if request.user.role != "STUDENT":

        return redirect(
            "accounts:dashboard"
        )

    proposals = (
        ProjectProposal.objects
        .filter(
            student=request.user
        )
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

    # Only students
    if request.user.role != "STUDENT":

        return redirect(
            "accounts:dashboard"
        )

    proposal_count = (
        ProjectProposal.objects
        .filter(
            student=request.user
        )
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

    if request.method == "POST":

        form = ProjectProposalForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            proposal = form.save(
                commit=False
            )

            proposal.student = request.user
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

        return redirect(
            "accounts:coordinator_dashboard"
        )

    # Only students
    if request.user.role != "STUDENT":

        return redirect(
            "accounts:dashboard"
        )

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
# EDIT / RESUBMIT PROJECT PROPOSAL AFTER CHANGES REQUESTED
# ============================================================

@login_required
def edit_proposal(request, proposal_id):

    if request.user.is_superuser:
        return redirect("accounts:coordinator_dashboard")

    if request.user.role != "STUDENT":
        return redirect("accounts:dashboard")

    proposal = get_object_or_404(
        ProjectProposal,
        id=proposal_id,
        student=request.user
    )

    if proposal.status not in ["SUBMITTED", "CHANGES_REQUESTED"]:
        messages.error(
            request,
            "This proposal cannot be edited in its current status."
        )
        return redirect("accounts:proposal_detail", proposal_id=proposal.id)

    if request.method == "POST":
        form = ProjectProposalForm(
            request.POST,
            request.FILES,
            instance=proposal,
        )

        if form.is_valid():
            updated_proposal = form.save(commit=False)
            updated_proposal.status = "SUBMITTED"
            updated_proposal.expert_comments = ""
            updated_proposal.save()

            messages.success(
                request,
                "Your proposal has been updated and resubmitted successfully."
            )

            return redirect(
                "accounts:proposal_detail",
                proposal_id=proposal.id
            )

        messages.error(
            request,
            "Please correct the errors in the form."
        )

    else:
        form = ProjectProposalForm(instance=proposal)

    return render(
        request,
        "student/proposal_form.html",
        {
            "form": form,
            "proposal": proposal,
            "proposal_count": ProjectProposal.objects.filter(student=request.user).count(),
            "is_edit_mode": True,
        },
    )


# ============================================================
# STUDENT WEEKLY PROGRESS
# ============================================================

@login_required
def student_progress(request):

    # --------------------------------------------------------
    # SUPERUSER → COORDINATOR
    # --------------------------------------------------------

    if request.user.is_superuser:

        return redirect(
            "accounts:coordinator_dashboard"
        )

    # --------------------------------------------------------
    # ONLY STUDENTS
    # --------------------------------------------------------

    if request.user.role != "STUDENT":

        return redirect(
            "accounts:dashboard"
        )

    # --------------------------------------------------------
    # FIND STUDENT'S APPROVED / ACTIVE PROJECT
    # --------------------------------------------------------

    project = (
        ProjectProposal.objects
        .filter(
            student=request.user,
            status__in=[
                "COORDINATOR_APPROVED",
                "GUIDE_ASSIGNED",
                "IN_PROGRESS",
                "COMPLETED",
            ]
        )
        .select_related(
            "guide"
        )
        .order_by("-updated_at")
        .first()
    )

    # --------------------------------------------------------
    # GET PROGRESS REPORTS
    # --------------------------------------------------------

    if project:

        progress_reports = (
            ProjectProgress.objects
            .filter(
                project=project,
                student=request.user
            )
            .order_by(
                "-week_number",
                "-submitted_at"
            )
        )

    else:

        progress_reports = ProjectProgress.objects.none()

    context = {
        "project": project,
        "progress_reports": progress_reports,
    }

    return render(
        request,
        "student/progress.html",
        context
    )


# ============================================================
# ADD WEEKLY PROGRESS
# ============================================================

@login_required
def add_progress(request):

    # --------------------------------------------------------
    # SUPERUSER → COORDINATOR
    # --------------------------------------------------------

    if request.user.is_superuser:

        return redirect(
            "accounts:coordinator_dashboard"
        )

    # --------------------------------------------------------
    # ONLY STUDENTS
    # --------------------------------------------------------

    if request.user.role != "STUDENT":

        return redirect(
            "accounts:dashboard"
        )

    # --------------------------------------------------------
    # FIND APPROVED / ACTIVE PROJECT
    # --------------------------------------------------------

    project = (
        ProjectProposal.objects
        .filter(
            student=request.user,
            status__in=[
                "COORDINATOR_APPROVED",
                "GUIDE_ASSIGNED",
                "IN_PROGRESS",
            ]
        )
        .select_related(
            "guide"
        )
        .order_by("-updated_at")
        .first()
    )

    # --------------------------------------------------------
    # PROJECT NOT APPROVED
    # --------------------------------------------------------

    if not project:

        messages.error(
            request,
            "You cannot upload weekly progress yet. "
            "Your project must be approved first."
        )

        return redirect(
            "accounts:student_progress"
        )

    # --------------------------------------------------------
    # GUIDE NOT ASSIGNED
    # --------------------------------------------------------

    if not project.guide:

        messages.error(
            request,
            "You cannot upload weekly progress until a guide is assigned."
        )

        return redirect(
            "accounts:student_progress"
        )

    # --------------------------------------------------------
    # POST
    # --------------------------------------------------------

    if request.method == "POST":

        form = ProjectProgressForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            progress = form.save(
                commit=False
            )

            # Automatically assign project
            progress.project = project

            # Automatically assign student
            progress.student = request.user

            # New report starts as submitted
            progress.status = "SUBMITTED"

            progress.save()

            messages.success(
                request,
                f"Week {progress.week_number} progress submitted successfully."
            )

            return redirect(
                "accounts:student_progress"
            )

        else:

            messages.error(
                request,
                "Please correct the errors in the form."
            )

            print("====================================")
            print("PROGRESS FORM ERRORS:")
            print(form.errors)
            print("====================================")

    # --------------------------------------------------------
    # GET
    # --------------------------------------------------------

    else:

        # Find latest submitted week
        last_progress = (
            ProjectProgress.objects
            .filter(
                project=project,
                student=request.user
            )
            .order_by("-week_number")
            .first()
        )

        # First progress = Week 1
        next_week = 1

        if last_progress:

            next_week = (
                last_progress.week_number + 1
            )

        form = ProjectProgressForm(
            initial={
                "week_number": next_week
            }
        )

    return render(
        request,
        "student/progress_form.html",
        {
            "form": form,
            "project": project,
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

            return redirect(
                "accounts:dashboard"
            )

    # --------------------------------------------------------
    # STUDENTS
    # --------------------------------------------------------

    students = (
        User.objects
        .filter(
            role="STUDENT"
        )
        .order_by("-date_joined")
    )

    # --------------------------------------------------------
    # ALL PROPOSALS
    # --------------------------------------------------------

    proposals = (
        ProjectProposal.objects
        .select_related(
            "student",
            "domain_expert",
            "guide"
        )
        .order_by("-submitted_at")
    )

    context = {

        "students": students,

        "student_count": students.count(),

        "proposals": proposals,

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

        "guide_assigned_count": proposals.filter(
            status="GUIDE_ASSIGNED"
        ).count(),

        "in_progress_count": proposals.filter(
            status="IN_PROGRESS"
        ).count(),

        "completed_count": proposals.filter(
            status="COMPLETED"
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

    # Superuser → Coordinator
    if request.user.is_superuser:

        return redirect(
            "accounts:coordinator_dashboard"
        )

    # Only experts
    if request.user.role != "EXPERT":

        return redirect(
            "accounts:dashboard"
        )

    proposals = (
        ProjectProposal.objects
        .filter(
            domain_expert=request.user
        )
        .select_related(
            "student"
        )
        .order_by("-submitted_at")
    )

    context = {

        "proposals": proposals,

        "proposal_count": proposals.count(),
    }

    return render(
        request,
        "experts/dashboard.html",
        context
    )


# ============================================================
# GUIDE DASHBOARD
# ============================================================

@login_required
def guide_dashboard(request):

    # Superuser → Coordinator
    if request.user.is_superuser:

        return redirect(
            "accounts:coordinator_dashboard"
        )

    # Only guides
    if request.user.role != "GUIDE":

        return redirect(
            "accounts:dashboard"
        )

    # --------------------------------------------------------
    # ASSIGNED PROJECTS
    # --------------------------------------------------------

    assigned_projects = (
        ProjectProposal.objects
        .filter(
            guide=request.user
        )
        .select_related(
            "student"
        )
        .order_by("-updated_at")
    )

    # --------------------------------------------------------
    # UNIQUE STUDENTS
    # --------------------------------------------------------

    student_count = (
        ProjectProposal.objects
        .filter(
            guide=request.user
        )
        .values(
            "student"
        )
        .distinct()
        .count()
    )

    # --------------------------------------------------------
    # PROJECT COUNT
    # --------------------------------------------------------

    project_count = assigned_projects.count()

    # --------------------------------------------------------
    # WEEKLY PROGRESS
    # --------------------------------------------------------

    pending_reviews = (
        ProjectProgress.objects
        .filter(
            project__guide=request.user,
            status="SUBMITTED"
        )
        .count()
    )

    reviewed_progress = (
        ProjectProgress.objects
        .filter(
            project__guide=request.user,
            status="REVIEWED"
        )
        .count()
    )

    changes_required = (
        ProjectProgress.objects
        .filter(
            project__guide=request.user,
            status="CHANGES_REQUIRED"
        )
        .count()
    )

    context = {

        "assigned_projects": assigned_projects,

        "student_count": student_count,

        "project_count": project_count,

        "pending_reviews": pending_reviews,

        "reviewed_progress": reviewed_progress,

        "changes_required": changes_required,
    }

    return render(
        request,
        "guide/dashboard.html",
        context
    )


# ============================================================
# GUIDE STUDENTS
# ============================================================

@login_required
def guide_students(request):

    # Superuser → Coordinator
    if request.user.is_superuser:

        return redirect(
            "accounts:coordinator_dashboard"
        )

    # Only guides
    if request.user.role != "GUIDE":

        return redirect(
            "accounts:dashboard"
        )

    assigned_projects = (
        ProjectProposal.objects
        .filter(
            guide=request.user
        )
        .select_related(
            "student"
        )
        .order_by("-updated_at")
    )

    context = {

        "assigned_projects": assigned_projects,
    }

    return render(
        request,
        "guide/students.html",
        context
    )


# ============================================================
# PANEL DASHBOARD
# ============================================================

@login_required
def panel_dashboard(request):

    # Superuser → Coordinator
    if request.user.is_superuser:

        return redirect(
            "accounts:coordinator_dashboard"
        )

    # Only panel members
    if request.user.role != "PANEL":

        return redirect(
            "accounts:dashboard"
        )

    return render(
        request,
        "panel/dashboard.html"
    )