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

from guides.models import GuideEvaluation


# ============================================================
# REPORT SEQUENCE
# ============================================================

REPORT_ORDER = [
    "PROGRESS_1",
    "PROGRESS_2",
    "PROGRESS_3",
    "FINAL_REPORT",
]


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
    # GET STUDENT PROPOSALS
    # --------------------------------------------------------

    proposals = (
        ProjectProposal.objects
        .filter(
            student=request.user
        )
        .select_related(
            "guide",
            "domain_expert"
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

    # ========================================================
    # ACTIVE PROJECT
    # ========================================================

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
            "guide",
            "domain_expert"
        )
        .order_by("-updated_at")
        .first()
    )

    # ========================================================
    # STUDENT WORKFLOW STATUS
    # ========================================================

    workflow_status_map = {
        "SUBMITTED": 1,
        "EXPERT_ASSIGNED": 2,
        "CHANGES_REQUESTED": 2,
        "EXPERT_APPROVED": 2,
        "COORDINATOR_APPROVED": 3,
        "GUIDE_ASSIGNED": 4,
        "GUIDE_REJECTED": 4,
        "IN_PROGRESS": 5,
        "COMPLETED": 10,
    }

    current_status = (
        project.status
        if project
        else "SUBMITTED"
    )

    current_workflow_step = workflow_status_map.get(
        current_status,
        1
    )

    workflow_steps = [

        {
            "number": 1,
            "title": "Submit Proposals",
            "description": "Student can submit up to 3 project proposals.",
            "state":
                "complete"
                if current_workflow_step > 1
                else "active"
                if current_status == "SUBMITTED"
                else "pending",
        },

        {
            "number": 2,
            "title": "Domain Expert Review",
            "description": "Domain Expert reviews the proposals and recommends one project.",
            "state":
                "complete"
                if current_workflow_step > 2
                else "active"
                if current_workflow_step == 2
                else "pending",
        },

        {
            "number": 3,
            "title": "Coordinator Approval",
            "description": "Coordinator gives final approval for the selected project.",
            "state":
                "complete"
                if current_workflow_step > 3
                else "active"
                if current_workflow_step == 3
                else "pending",
        },

        {
            "number": 4,
            "title": "Guide Assignment",
            "description": "Coordinator assigns a Guide to the approved project.",
            "state":
                "complete"
                if current_workflow_step > 4
                else "active"
                if current_workflow_step == 4
                else "pending",
        },

        {
            "number": 5,
            "title": "Project Progress",
            "description": "Student completes project progress work and the required reports.",
            "state":
                "complete"
                if current_workflow_step > 5
                else "active"
                if current_workflow_step == 5
                else "pending",
        },

        {
            "number": 6,
            "title": "Final Report",
            "description": "Student submits the final report for assessment.",
            "state":
                "complete"
                if current_workflow_step >= 10
                else "active"
                if current_workflow_step == 6
                else "pending",
        },

        {
            "number": 7,
            "title": "Final Evaluation",
            "description": "Guide reviews the Final Report and enters the project mark.",
            "state":
                "complete"
                if current_workflow_step >= 10
                else "active"
                if current_workflow_step == 7
                else "pending",
        },

        {
            "number": 8,
            "title": "Project Completed",
            "description": "Final mark is available in the Final Mark page and the project is completed.",
            "state":
                "complete"
                if current_workflow_step >= 10
                else "active"
                if current_workflow_step == 8
                else "pending",
        },
    ]

    # ========================================================
    # CONTEXT
    # ========================================================

    context = {

        "proposals": proposals,

        "proposal_count": proposal_count,

        "pending_count": pending_count,

        "approved_count": approved_count,

        "current_workflow_step": current_workflow_step,

        "current_workflow_status": current_status,

        "current_workflow_status_display":
            project.get_status_display()
            if project
            else "Not Started",

        "workflow_steps": workflow_steps,

        # Active project
        "project": project,
    }

    return render(
        request,
        "student/dashboard.html",
        context
    )


# ============================================================
# STUDENT FINAL MARK
# ============================================================

@login_required
def student_final_mark(request):

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
    # GET STUDENT FINAL EVALUATION
    # --------------------------------------------------------

    evaluation = (
        GuideEvaluation.objects
        .filter(
            project__student=request.user
        )
        .select_related(
            "project",
            "guide"
        )
        .order_by("-updated_at")
        .first()
    )

    # --------------------------------------------------------
    # CONTEXT
    # --------------------------------------------------------

    context = {
        "evaluation": evaluation,
    }

    return render(
        request,
        "student/final_mark.html",
        context
    )


# ============================================================
# STUDENT PROPOSALS
# ============================================================

@login_required
def student_proposals(request):

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

    # --------------------------------------------------------
    # ONLY STUDENTS
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # MAXIMUM 3 PROPOSALS
    # --------------------------------------------------------

    if proposal_count >= 3:

        messages.error(
            request,
            "You have already submitted the maximum of 3 proposals."
        )

        return redirect(
            "accounts:student_proposals"
        )

    # --------------------------------------------------------
    # POST
    # --------------------------------------------------------

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

        messages.error(
            request,
            "Please correct the errors in the form."
        )

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
# EDIT / RESUBMIT PROJECT PROPOSAL
# ============================================================

@login_required
def edit_proposal(request, proposal_id):

    # --------------------------------------------------------
    # SUPERUSER
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

    proposal = get_object_or_404(
        ProjectProposal,
        id=proposal_id,
        student=request.user
    )

    # --------------------------------------------------------
    # CHECK STATUS
    # --------------------------------------------------------

    if proposal.status not in [
        "SUBMITTED",
        "CHANGES_REQUESTED",
    ]:

        messages.error(
            request,
            "This proposal cannot be edited in its current status."
        )

        return redirect(
            "accounts:proposal_detail",
            proposal_id=proposal.id
        )

    # --------------------------------------------------------
    # POST
    # --------------------------------------------------------

    if request.method == "POST":

        form = ProjectProposalForm(
            request.POST,
            request.FILES,
            instance=proposal,
        )

        if form.is_valid():

            updated_proposal = form.save(
                commit=False
            )

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

        form = ProjectProposalForm(
            instance=proposal
        )

    return render(
        request,
        "student/proposal_form.html",
        {
            "form": form,

            "proposal": proposal,

            "proposal_count": (
                ProjectProposal.objects
                .filter(
                    student=request.user
                )
                .count()
            ),

            "is_edit_mode": True,
        },
    )


# ============================================================
# STUDENT PROGRESS
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
    # FIND ACTIVE PROJECT
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
            "guide",
            "domain_expert"
        )
        .order_by("-updated_at")
        .first()
    )

    # --------------------------------------------------------
    # NO PROJECT
    # --------------------------------------------------------

    if not project:

        return render(
            request,
            "student/progress.html",
            {
                "project": None,
                "progress_reports": [],
                "evaluation": None,
                "can_upload": False,
                "next_report": None,
            }
        )

    # --------------------------------------------------------
    # GET REPORTS
    # --------------------------------------------------------

    progress_reports = (
        ProjectProgress.objects
        .filter(
            project=project,
            student=request.user
        )
        .order_by("submitted_at")
    )

    # --------------------------------------------------------
    # GET FINAL EVALUATION
    # --------------------------------------------------------

    evaluation = getattr(
        project,
        "guide_evaluation",
        None
    )

    # --------------------------------------------------------
    # REPORT MAP
    # --------------------------------------------------------

    report_map = {
        report.report_type: report
        for report in progress_reports
    }

    # --------------------------------------------------------
    # DETERMINE NEXT REPORT
    # --------------------------------------------------------

    next_report = None

    can_upload = False

    # --------------------------------------------------------
    # CHANGES REQUIRED HAS FIRST PRIORITY
    # --------------------------------------------------------

    for report_type in REPORT_ORDER:

        report = report_map.get(
            report_type
        )

        if report and report.status == "CHANGES_REQUIRED":

            next_report = report_type

            can_upload = True

            break

    # --------------------------------------------------------
    # NORMAL REPORT SEQUENCE
    # --------------------------------------------------------

    if next_report is None:

        for index, report_type in enumerate(
            REPORT_ORDER
        ):

            # ------------------------------------------------
            # REPORT DOES NOT EXIST
            # ------------------------------------------------

            if report_type not in report_map:

                # First report
                if index == 0:

                    next_report = report_type

                    can_upload = True

                else:

                    previous_type = REPORT_ORDER[
                        index - 1
                    ]

                    previous_report = report_map.get(
                        previous_type
                    )

                    # Previous report must be reviewed
                    if (
                        previous_report
                        and previous_report.status == "REVIEWED"
                    ):

                        next_report = report_type

                        can_upload = True

                break

    # --------------------------------------------------------
    # CONTEXT
    # --------------------------------------------------------

    context = {

        "project": project,

        "progress_reports": progress_reports,

        "evaluation": evaluation,

        "next_report": next_report,

        "can_upload": can_upload,
    }

    return render(
        request,
        "student/progress.html",
        context
    )


# ============================================================
# ADD / RESUBMIT PROGRESS REPORT
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
    # FIND ACTIVE PROJECT
    # --------------------------------------------------------

    project = (
        ProjectProposal.objects
        .filter(
            student=request.user,
            status__in=[
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
    # PROJECT NOT FOUND
    # --------------------------------------------------------

    if not project:

        messages.error(
            request,
            "You cannot upload progress yet. "
            "Your project must be approved and assigned to a guide."
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
            "You cannot upload progress until a guide is assigned."
        )

        return redirect(
            "accounts:student_progress"
        )

    # --------------------------------------------------------
    # PROJECT MUST BE IN PROGRESS
    # --------------------------------------------------------

    if project.status != "IN_PROGRESS":

        messages.warning(
            request,
            "Your Guide must start the project before you can upload progress."
        )

        return redirect(
            "accounts:student_progress"
        )

    # --------------------------------------------------------
    # GET EXISTING REPORTS
    # --------------------------------------------------------

    reports = list(
        ProjectProgress.objects
        .filter(
            project=project,
            student=request.user
        )
        .order_by("submitted_at")
    )

    report_map = {
        report.report_type: report
        for report in reports
    }

    # --------------------------------------------------------
    # TARGET REPORT
    # --------------------------------------------------------

    target_report_type = None

    target_instance = None

    # --------------------------------------------------------
    # CHANGES REQUIRED FIRST
    # --------------------------------------------------------

    for report_type in REPORT_ORDER:

        report = report_map.get(
            report_type
        )

        if report and report.status == "CHANGES_REQUIRED":

            target_report_type = report_type

            target_instance = report

            break

    # --------------------------------------------------------
    # NORMAL SEQUENCE
    # --------------------------------------------------------

    if target_report_type is None:

        for index, report_type in enumerate(
            REPORT_ORDER
        ):

            # ------------------------------------------------
            # FIRST MISSING REPORT
            # ------------------------------------------------

            if report_type not in report_map:

                # First report
                if index == 0:

                    target_report_type = report_type

                else:

                    previous_type = REPORT_ORDER[
                        index - 1
                    ]

                    previous_report = report_map.get(
                        previous_type
                    )

                    # Previous report must be reviewed
                    if (
                        previous_report
                        and previous_report.status == "REVIEWED"
                    ):

                        target_report_type = report_type

                    else:

                        messages.warning(
                            request,
                            "You must wait until the previous report "
                            "is reviewed by the Guide."
                        )

                        return redirect(
                            "accounts:student_progress"
                        )

                break

    # --------------------------------------------------------
    # ALL REPORTS COMPLETED
    # --------------------------------------------------------

    if target_report_type is None:

        messages.info(
            request,
            "All four project reports have already been submitted."
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
            request.FILES,
            instance=target_instance
        )

        if form.is_valid():

            progress = form.save(
                commit=False
            )

            # Automatically assign project
            progress.project = project

            # Automatically assign student
            progress.student = request.user

            # Backend controls report type
            progress.report_type = target_report_type

            # Every submission starts as SUBMITTED
            progress.status = "SUBMITTED"

            # Clear old review timestamp
            progress.reviewed_at = None

            progress.save()

            report_name = dict(
                ProjectProgress.REPORT_CHOICES
            ).get(
                target_report_type,
                target_report_type
            )

            if target_instance:

                messages.success(
                    request,
                    f"{report_name} resubmitted successfully."
                )

            else:

                messages.success(
                    request,
                    f"{report_name} submitted successfully."
                )

            return redirect(
                "accounts:student_progress"
            )

        messages.error(
            request,
            "Please correct the errors in the form."
        )

    else:

        form = ProjectProgressForm(
            instance=target_instance
        )

    # --------------------------------------------------------
    # REPORT NAME
    # --------------------------------------------------------

    report_name = dict(
        ProjectProgress.REPORT_CHOICES
    ).get(
        target_report_type,
        target_report_type
    )

    return render(
        request,
        "student/progress_form.html",
        {
            "form": form,

            "project": project,

            "report_type": target_report_type,

            "report_name": report_name,

            "is_resubmission": (
                target_instance is not None
            ),
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

    # --------------------------------------------------------
    # CONTEXT
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # SUPERUSER → COORDINATOR
    # --------------------------------------------------------

    if request.user.is_superuser:

        return redirect(
            "accounts:coordinator_dashboard"
        )

    # --------------------------------------------------------
    # ONLY EXPERTS
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # SUPERUSER → COORDINATOR
    # --------------------------------------------------------

    if request.user.is_superuser:

        return redirect(
            "accounts:coordinator_dashboard"
        )

    # --------------------------------------------------------
    # ONLY GUIDES
    # --------------------------------------------------------

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
    # PROGRESS REVIEW COUNTS
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

    # --------------------------------------------------------
    # SUPERUSER → COORDINATOR
    # --------------------------------------------------------

    if request.user.is_superuser:

        return redirect(
            "accounts:coordinator_dashboard"
        )

    # --------------------------------------------------------
    # ONLY GUIDES
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # SUPERUSER → COORDINATOR
    # --------------------------------------------------------

    if request.user.is_superuser:

        return redirect(
            "accounts:coordinator_dashboard"
        )

    # --------------------------------------------------------
    # ONLY PANEL MEMBERS
    # --------------------------------------------------------

    if request.user.role != "PANEL":

        return redirect(
            "accounts:dashboard"
        )

    return render(
        request,
        "panel/dashboard.html"
    )