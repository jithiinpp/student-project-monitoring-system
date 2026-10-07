from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch
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
    PanelEvaluation,
    ProjectMessage,
)

from guides.models import GuideEvaluation


# ============================================================
# REPORT SEQUENCE
# ============================================================

REPORT_ORDER = [
    "PROGRESS_1",
    "PROGRESS_2",
    "PROGRESS_3",
]


def _panel_projects_with_final_reports():
    final_reports = (
        ProjectProgress.objects
        .filter(report_type="FINAL_REPORT")
        .order_by("-submitted_at")
    )
    return (
        ProjectProposal.objects
        .filter(progress_reports__report_type="FINAL_REPORT")
        .select_related("student", "guide", "panel_evaluation")
        .prefetch_related(
            Prefetch(
                "progress_reports",
                queryset=final_reports,
                to_attr="panel_final_reports",
            )
        )
        .distinct()
        .order_by("-updated_at")
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
            user.is_student=True

            user.save(
                update_fields=["is_student"]
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

    roles = []
    
    if user.is_superuser or user.is_coordinator:
        roles.append({
            "name": "Coordinator",
            "url_name": "coordinator:dashboard",
            "icon": '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>',
            "desc": "Manage students, experts, guides and oversee all projects."
        })
        
    if user.is_expert:
        roles.append({
            "name": "Domain Expert",
            "url_name": "experts:dashboard",
            "icon": '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 16 16 12 12 8"></polyline><line x1="8" y1="12" x2="16" y2="12"></line></svg>',
            "desc": "Review proposals and evaluate project viability."
        })
        
    if user.is_guide:
        roles.append({
            "name": "Guide",
            "url_name": "guides:dashboard",
            "icon": '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"></path><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"></path></svg>',
            "desc": "Guide students, approve changes, and monitor weekly progress."
        })
        
    if user.is_panel:
        roles.append({
            "name": "Panel Member",
            "url_name": "accounts:panel_dashboard",
            "icon": '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>',
            "desc": "Evaluate final projects and submit marks."
        })
        
    if user.is_student:
        roles.append({
            "name": "Student",
            "url_name": "accounts:student_dashboard",
            "icon": '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 10v6M2 10l10-5 10 5-10 5z"></path><path d="M6 12v5c3 3 9 3 12 0v-5"></path></svg>',
            "desc": "Submit proposals, weekly progress, and view grades."
        })

    if len(roles) > 1:
        return render(request, "accounts/role_selection.html", {"roles": roles})
    elif len(roles) == 1:
        return redirect(roles[0]["url_name"])

    # INVALID ROLE
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

    if not request.user.is_student:

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

    changes_requested_count = proposals.filter(
        status="CHANGES_REQUESTED"
    ).count()

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
            "description": "Guide and Panel review the Final Report and enter the project marks.",
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
    # MESSAGES
    # ========================================================

    project_messages = []
    if project:
        project_messages = project.messages.select_related("sender").all()

    # ========================================================
    # CONTEXT
    # ========================================================
    
    from coordinator.models import ScheduleDocument
    latest_schedule_doc = ScheduleDocument.objects.first()

    context = {

        "proposals": proposals,

        "proposal_count": proposal_count,

        "pending_count": pending_count,

        "changes_requested_count": changes_requested_count,

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
        
        "project_messages": project_messages,
        
        "scheduled_reviews": proposals.exclude(review_date__isnull=True).order_by("review_date"),
        
        "latest_schedule_doc": latest_schedule_doc,
    }

    return render(
        request,
        "student/dashboard.html",
        context
    )


# =========================================================
# STUDENT SCHEDULE
# =========================================================

@login_required
def student_schedule(request):
    if not getattr(request.user, 'is_student', False):
        return redirect("accounts:login")
        
    from coordinator.models import ScheduleDocument
    from projects.models import ProjectProposal
    
    latest_schedule_doc = ScheduleDocument.objects.first()
    
    scheduled_reviews = ProjectProposal.objects.filter(
        student=request.user,
        review_date__isnull=False
    ).order_by('review_date')
    
    context = {
        "latest_schedule_doc": latest_schedule_doc,
        "scheduled_reviews": scheduled_reviews,
    }
    
    return render(
        request,
        "student/schedule.html",
        context
    )


# ============================================================
# STUDENT SEND MESSAGE
# ============================================================

@login_required
def student_send_message(request, project_id):
    if not request.user.is_student:
        return redirect("accounts:dashboard")
        
    if request.method == "POST":
        project = get_object_or_404(ProjectProposal, id=project_id, student=request.user)
        message_text = request.POST.get("message", "").strip()
        if message_text:
            ProjectMessage.objects.create(
                project=project,
                sender=request.user,
                message=message_text
            )
        referer = request.META.get('HTTP_REFERER')
        if referer:
            return redirect(referer)
        return redirect("accounts:student_dashboard")
    return redirect("accounts:dashboard")


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

    if not request.user.is_student:

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

    panel_evaluation = (
        PanelEvaluation.objects
        .filter(
            project__student=request.user
        )
        .select_related(
            "project",
            "panel_member"
        )
        .order_by("-updated_at")
        .first()
    )

    # --------------------------------------------------------
    # CONTEXT
    # --------------------------------------------------------

    context = {
        "evaluation": evaluation,
        "panel_evaluation": panel_evaluation,
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

    if not request.user.is_student:

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

    filter_type = request.GET.get("filter")

    if filter_type == "under_review":
        proposals = proposals.filter(
            status__in=[
                "SUBMITTED",
                "EXPERT_ASSIGNED",
                "CHANGES_REQUESTED"
            ]
        )
    elif filter_type == "approved":
        proposals = proposals.filter(
            status__in=[
                "EXPERT_APPROVED",
                "COORDINATOR_APPROVED",
                "GUIDE_ASSIGNED",
                "IN_PROGRESS",
                "COMPLETED"
            ]
        )
    elif filter_type == "changes_requested":
        proposals = proposals.filter(
            status="CHANGES_REQUESTED"
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

    if not request.user.is_student:

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

    if not request.user.is_student:

        return redirect(
            "accounts:dashboard"
        )

    proposal = get_object_or_404(
        ProjectProposal,
        id=proposal_id,
        student=request.user
    )

    latest_change_request = proposal.change_requests.order_by('-created_at').first()

    return render(
        request,
        "student/proposal_detail.html",
        {
            "proposal": proposal,
            "latest_change_request": latest_change_request
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

    if not request.user.is_student:

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

    if not request.user.is_student:

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
    # MESSAGES
    # --------------------------------------------------------

    project_messages = project.messages.select_related("sender").all()

    # --------------------------------------------------------
    # CONTEXT
    # --------------------------------------------------------

    context = {

        "project": project,

        "project_messages": project_messages,

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
# STUDENT WEEKLY REPORTS
# ============================================================

@login_required
def student_weekly_reports(request):
    if not request.user.is_student:
        return redirect("accounts:dashboard")
    
    project = ProjectProposal.objects.filter(
        student=request.user,
        status__in=["COORDINATOR_APPROVED", "GUIDE_ASSIGNED", "IN_PROGRESS", "COMPLETED"]
    ).select_related("guide", "domain_expert").order_by("-updated_at").first()
    
    if not project:
        return render(request, "student/weekly_reports.html", {"project": None, "reports": []})
        
    reports = ProjectProgress.objects.filter(
        project=project,
        student=request.user,
        report_type__in=["PROGRESS_1", "PROGRESS_2", "PROGRESS_3"]
    ).order_by("submitted_at")
    
    return render(request, "student/weekly_reports.html", {
        "project": project,
        "reports": reports
    })

# ============================================================
# STUDENT FINAL REPORTS
# ============================================================

@login_required
def student_final_reports(request):
    if not request.user.is_student:
        return redirect("accounts:dashboard")
        
    project = ProjectProposal.objects.filter(
        student=request.user,
        status__in=["COORDINATOR_APPROVED", "GUIDE_ASSIGNED", "IN_PROGRESS", "COMPLETED"]
    ).select_related("guide", "domain_expert").order_by("-updated_at").first()
    
    if not project:
        return render(request, "student/final_reports.html", {"project": None, "reports": []})
        
    reports = ProjectProgress.objects.filter(
        project=project,
        student=request.user,
        report_type="FINAL_REPORT"
    ).order_by("submitted_at")
    
    return render(request, "student/final_reports.html", {
        "project": project,
        "reports": reports
    })


# ============================================================
# STUDENT DISCUSSION
# ============================================================

@login_required
def student_discussion(request):
    if not request.user.is_student:
        return redirect("accounts:dashboard")
        
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
        .select_related("guide")
        .order_by("-updated_at")
        .first()
    )
    
    project_messages = []
    if project:
        project_messages = project.messages.select_related("sender").all()
        
    context = {
        "project": project,
        "project_messages": project_messages,
    }
    
    return render(
        request,
        "student/discussion.html",
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

    if not request.user.is_student:

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

    expected_week_number = {
        "PROGRESS_1": 1,
        "PROGRESS_2": 2,
        "PROGRESS_3": 3,
    }[target_report_type]

    if request.method == "POST":

        form = ProjectProgressForm(
            request.POST,
            request.FILES,
            instance=target_instance,
            require_week_number=True,
            expected_week_number=expected_week_number,
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
            instance=target_instance,
            require_week_number=True,
            expected_week_number=expected_week_number,
            initial={"week_number": expected_week_number},
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
# ADD / RESUBMIT FINAL REPORT
# ============================================================

@login_required
def add_final_report(request):

    if request.user.is_superuser:
        return redirect("accounts:coordinator_dashboard")

    if not request.user.is_student:
        return redirect("accounts:dashboard")

    project = (
        ProjectProposal.objects
        .filter(
            student=request.user,
            status__in=["GUIDE_ASSIGNED", "IN_PROGRESS", "COMPLETED"]
        )
        .select_related("guide")
        .order_by("-updated_at")
        .first()
    )

    if not project:
        messages.error(request, "You cannot upload progress yet. Your project must be approved.")
        return redirect("accounts:student_progress")

    if not project.guide:
        messages.error(request, "You cannot upload progress until a guide is assigned.")
        return redirect("accounts:student_progress")

    if project.status not in ["IN_PROGRESS", "COMPLETED"]:
        messages.warning(request, "Your Guide must start the project before you can upload the final report.")
        return redirect("accounts:student_progress")

    target_instance = ProjectProgress.objects.filter(
        project=project,
        student=request.user,
        report_type="FINAL_REPORT"
    ).first()

    if target_instance and target_instance.status == "REVIEWED":
        messages.warning(request, "Your Final Report has already been reviewed and cannot be changed.")
        return redirect("accounts:student_progress")

    if request.method == "POST":
        form = ProjectProgressForm(request.POST, request.FILES, instance=target_instance)
        if form.is_valid():
            progress = form.save(commit=False)
            progress.project = project
            progress.student = request.user
            progress.report_type = "FINAL_REPORT"
            progress.week_number = None
            progress.status = "SUBMITTED"
            progress.reviewed_at = None
            progress.save()

            if target_instance:
                messages.success(request, "Final Report resubmitted successfully.")
            else:
                messages.success(request, "Final Report submitted successfully.")
            return redirect("accounts:student_progress")
        messages.error(request, "Please correct the errors in the form.")
    else:
        form = ProjectProgressForm(instance=target_instance)

    return render(
        request,
        "student/progress_form.html",
        {
            "form": form,
            "project": project,
            "report_type": "FINAL_REPORT",
            "report_name": "Final Report",
            "is_resubmission": (target_instance is not None),
        }
    )


# ============================================================
# COORDINATOR DASHBOARD
# ============================================================

@login_required
def coordinator_dashboard(request):

    # Superuser allowed
    if not request.user.is_superuser:

        if not request.user.is_coordinator:

            return redirect(
                "accounts:dashboard"
            )

    # --------------------------------------------------------
    # STUDENTS
    # --------------------------------------------------------

    students = (
        User.objects
        .filter(
            is_student=True
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

    if not request.user.is_expert:

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

    if not request.user.is_guide:

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

    if not request.user.is_guide:

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

    if not request.user.is_panel:

        return redirect(
            "accounts:dashboard"
        )

    projects = _panel_projects_with_final_reports()
    student_count = User.objects.filter(
        is_student=True,
        is_superuser=False,
    ).count()
    
    pending_count = projects.filter(panel_evaluation__isnull=True).count()
    completed_count = projects.filter(panel_evaluation__isnull=False).count()

    context = {
        "projects": projects,
        "total_projects": projects.count(),
        "student_count": student_count,
        "pending_count": pending_count,
        "completed_count": completed_count,
    }

    return render(
        request,
        "panel/dashboard.html",
        context
    )

# ============================================================
# PANEL SCHEDULE
# ============================================================

@login_required
def panel_schedule(request):
    if not request.user.is_panel:
        return redirect("accounts:dashboard")
        
    from coordinator.models import ScheduleDocument
    from projects.models import ProjectProposal
    
    latest_schedule_doc = ScheduleDocument.objects.first()
    
    scheduled_reviews = ProjectProposal.objects.filter(
        review_date__isnull=False
    ).order_by('review_date')
    
    context = {
        "latest_schedule_doc": latest_schedule_doc,
        "scheduled_reviews": scheduled_reviews,
    }
    
    return render(
        request,
        "panel/schedule.html",
        context
    )

@login_required
def panel_evaluations(request):
    if not request.user.is_panel:
        return redirect("accounts:dashboard")

    context = {
        "projects": _panel_projects_with_final_reports(),
    }

    return render(
        request,
        "panel/evaluations.html",
        context
    )

@login_required
def panel_students(request):
    if not request.user.is_panel:
        return redirect("accounts:dashboard")

    final_reports = ProjectProgress.objects.filter(
        report_type="FINAL_REPORT"
    ).order_by("-submitted_at")
    student_projects = (
        ProjectProposal.objects
        .exclude(status="REJECTED")
        .select_related("panel_evaluation", "guide")
        .prefetch_related(
            Prefetch(
                "progress_reports",
                queryset=final_reports,
                to_attr="panel_final_reports",
            )
        )
        .order_by("-updated_at")
    )
    students = (
        User.objects
        .filter(is_student=True, is_superuser=False)
        .prefetch_related(
            Prefetch(
                "project_proposals",
                queryset=student_projects,
                to_attr="panel_projects",
            )
        )
        .order_by("first_name", "last_name", "username")
    )

    return render(
        request,
        "panel/students.html",
        {
            "students": students,
            "student_count": students.count(),
        }
    )

@login_required
def panel_evaluate(request, project_id):
    if not request.user.is_panel:
        return redirect("accounts:dashboard")
        
    project = get_object_or_404(
        ProjectProposal.objects.select_related(
            "student",
            "guide",
            "panel_evaluation",
        ),
        id=project_id,
        progress_reports__report_type="FINAL_REPORT",
    )

    final_report = project.progress_reports.filter(
        report_type="FINAL_REPORT"
    ).order_by("-submitted_at").first()
    if not final_report:
        messages.error(request, "This project does not have a final report yet.")
        return redirect("accounts:panel_dashboard")
        
    evaluation = getattr(project, "panel_evaluation", None)
    
    if request.method == "POST":
        feedback = request.POST.get("feedback", "").strip()
        titles = request.POST.getlist("criteria_title[]")
        marks = request.POST.getlist("criteria_mark[]")

        if len(titles) != len(marks):
            messages.error(request, "Each mark category must have a matching mark.")
            return redirect("accounts:panel_evaluate", project_id=project.id)

        detailed_marks = {}
        total_marks = Decimal("0")

        for title_text, mark_text in zip(titles, marks):
            title = title_text.strip()
            mark_text = mark_text.strip()

            if not title and not mark_text:
                continue
            if not title or not mark_text:
                messages.error(
                    request,
                    "Enter both a category name and mark for every row.",
                )
                return redirect("accounts:panel_evaluate", project_id=project.id)
            if title in detailed_marks:
                messages.error(request, "Mark category names must be unique.")
                return redirect("accounts:panel_evaluate", project_id=project.id)

            try:
                mark_value = Decimal(mark_text)
            except InvalidOperation:
                messages.error(request, "Enter a valid number for each mark.")
                return redirect("accounts:panel_evaluate", project_id=project.id)

            if (
                not mark_value.is_finite()
                or mark_value < 0
                or mark_value > 100
                or mark_value.as_tuple().exponent < -2
            ):
                messages.error(
                    request,
                    "Each mark must be between 0 and 100 with at most two decimal places.",
                )
                return redirect("accounts:panel_evaluate", project_id=project.id)

            detailed_marks[title] = str(mark_value)
            total_marks += mark_value

        if not detailed_marks:
            messages.error(request, "Add at least one mark category.")
            return redirect("accounts:panel_evaluate", project_id=project.id)

        if total_marks > 100:
            messages.error(request, "Total marks cannot exceed 100.")
            return redirect("accounts:panel_evaluate", project_id=project.id)

        if not evaluation:
            evaluation = PanelEvaluation(project=project, panel_member=request.user)
            
        evaluation.feedback = feedback
        evaluation.detailed_marks = detailed_marks
        evaluation.marks = total_marks
        evaluation.panel_member = request.user
        evaluation.save()

        messages.success(request, "Panel evaluation saved successfully.")
        return redirect("accounts:panel_dashboard")
    return render(request, "panel/evaluate.html", {
        "project": project,
        "final_report": final_report,
        "evaluation": evaluation,
    })

@login_required
def panel_send_message(request, project_id):
    if not request.user.is_panel:
        return redirect("accounts:dashboard")
        
    if request.method == "POST":
        project = get_object_or_404(ProjectProposal, id=project_id)
        message_text = request.POST.get("message", "").strip()
        if message_text:
            from projects.models import ProjectMessage
            ProjectMessage.objects.create(
                project=project,
                sender=request.user,
                message=message_text
            )
        referer = request.META.get('HTTP_REFERER')
        if referer:
            return redirect(referer)
        return redirect("accounts:panel_evaluate", project_id=project_id)
    return redirect("accounts:dashboard")

@login_required
def student_profile(request, student_id):
    from django.shortcuts import get_object_or_404
    from .models import User
    
    if not (request.user.is_superuser or request.user.is_coordinator or request.user.is_expert or request.user.is_guide or request.user.is_panel):
        messages.error(request, "You do not have permission to view this profile.")
        return redirect("accounts:dashboard")
        
    student = get_object_or_404(User, id=student_id, is_student=True)
    
    # We could also fetch their active project
    from projects.models import ProjectProposal
    project = ProjectProposal.objects.filter(student=student).order_by('-updated_at').first()
    
    guides = None
    if request.user.is_coordinator:
        guides = User.objects.filter(is_guide=True, is_active=True, is_superuser=False)

    return render(request, "accounts/student_profile.html", {
        "student": student,
        "project": project,
        "guides": guides
    })