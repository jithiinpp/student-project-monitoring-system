from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch, Q
from django.http import Http404
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
    PanelMarkCriterion,
    ProjectMessage,
)

from guides.models import GuideEvaluation


# ============================================================
# REPORT SEQUENCE
# ============================================================

WEEKLY_REPORT_TYPES = ("PROGRESS_1", "PROGRESS_2", "PROGRESS_3")
WEEKLY_REPORT_TYPE_BY_NUMBER = {
    1: "PROGRESS_1",
    2: "PROGRESS_2",
}


def _weekly_report_number(report):
    if report.week_number is not None:
        return report.week_number
    return {
        "PROGRESS_1": 1,
        "PROGRESS_2": 2,
        "PROGRESS_3": 3,
    }.get(report.report_type, 0)


def _next_weekly_report(reports):
    weekly_reports = [
        report
        for report in reports
        if report.report_type in WEEKLY_REPORT_TYPES
    ]

    changes_report = next(
        (
            report
            for report in sorted(weekly_reports, key=_weekly_report_number)
            if report.status == "CHANGES_REQUIRED"
        ),
        None,
    )
    if changes_report:
        return (
            changes_report.report_type,
            _weekly_report_number(changes_report),
            changes_report,
            True,
        )

    if not weekly_reports:
        return "PROGRESS_1", 1, None, True

    latest_report = max(
        weekly_reports,
        key=lambda report: (
            _weekly_report_number(report),
            report.submitted_at,
        ),
    )
    latest_week_number = _weekly_report_number(latest_report)
    if latest_report.status != "REVIEWED":
        return None, latest_week_number, None, False

    next_week_number = latest_week_number + 1
    next_report_type = WEEKLY_REPORT_TYPE_BY_NUMBER.get(
        next_week_number,
        "PROGRESS_3",
    )
    return next_report_type, next_week_number, None, True


def _panel_projects_with_final_reports(panel_member):
    final_reports = (
        ProjectProgress.objects
        .filter(report_type="FINAL_REPORT")
        .order_by("-submitted_at")
    )
    return (
        ProjectProposal.objects
        .filter(progress_reports__report_type="FINAL_REPORT")
        .filter(
            Q(panel_members=panel_member)
            | Q(panel_members__isnull=True)
        )
        .select_related("student", "guide")
        .prefetch_related(
            Prefetch(
                "panel_reviews",
                queryset=PanelEvaluation.objects.filter(
                    panel_member=panel_member
                ).order_by("review_number"),
                to_attr="panel_review_list",
            )
        )
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

    panel_evaluations = (
        PanelEvaluation.objects
        .filter(
            project__student=request.user
        )
        .select_related(
            "project",
            "panel_member"
        )
        .order_by("review_number", "panel_member_id")
    )

    if evaluation:
        mark_project = evaluation.project
    elif panel_evaluations.exists():
        mark_project = panel_evaluations.first().project
    else:
        mark_project = (
            ProjectProposal.objects
            .filter(
                student=request.user,
                status__in=[
                    "COORDINATOR_APPROVED",
                    "GUIDE_ASSIGNED",
                    "IN_PROGRESS",
                    "COMPLETED",
                ],
            )
            .order_by("-updated_at")
            .first()
        )

    report_marks = (
        ProjectProgress.objects
        .filter(
            project=mark_project,
            student=request.user,
            report_type__in=[
                "PROGRESS_1",
                "PROGRESS_2",
                "PROGRESS_3",
                "FINAL_REPORT",
            ],
        )
        .select_related("project")
        .order_by("submitted_at")
        if mark_project
        else ProjectProgress.objects.none()
    )

    # --------------------------------------------------------
    # CONTEXT
    # --------------------------------------------------------

    panel_evaluation_list = (
        list(panel_evaluations.filter(project=mark_project))
        if mark_project
        else []
    )
    panel_evaluations_by_number = {}
    for panel_evaluation in panel_evaluation_list:
        panel_evaluations_by_number.setdefault(
            panel_evaluation.review_number,
            [],
        ).append(panel_evaluation)

    panel_reviews = []
    for review_number in (1, 2, 3):
        evaluations_for_review = panel_evaluations_by_number.get(
            review_number,
            [],
        )
        average_mark = None
        average_detailed_marks = {}

        if evaluations_for_review:
            average_mark = (
                sum(
                    (item.marks for item in evaluations_for_review),
                    Decimal("0"),
                )
                / len(evaluations_for_review)
            ).quantize(Decimal("0.01"))

            category_values = {}
            for item in evaluations_for_review:
                for category, mark in item.detailed_marks.items():
                    category_values.setdefault(category, []).append(
                        Decimal(str(mark))
                    )

            average_detailed_marks = {
                category: (
                    sum(values, Decimal("0")) / len(values)
                ).quantize(Decimal("0.01"))
                for category, values in category_values.items()
            }

        panel_reviews.append(
            {
                "number": review_number,
                "evaluation": (
                    evaluations_for_review[0]
                    if evaluations_for_review
                    else None
                ),
                "evaluations": evaluations_for_review,
                "average_mark": average_mark,
                "average_detailed_marks": average_detailed_marks,
                "panel_count": len(evaluations_for_review),
            }
        )

    context = {
        "evaluation": evaluation,
        "panel_evaluations": panel_evaluation_list,
        "panel_reviews": panel_reviews,
        "mark_project": mark_project,
        "report_marks": report_marks,
        "panel_max_mark": (
            sum(
                PanelMarkCriterion.objects.values_list("max_marks", flat=True),
                Decimal("0"),
            )
            or Decimal("100")
        ),
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

    next_report, next_week_number, _, can_upload = (
        _next_weekly_report(list(progress_reports))
    )

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

        "next_week_number": next_week_number,

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
        
    reports = list(ProjectProgress.objects.filter(
        project=project,
        student=request.user,
        report_type__in=WEEKLY_REPORT_TYPES
    ).order_by("submitted_at"))
    _, next_week_number, _, can_upload = _next_weekly_report(reports)
    
    return render(request, "student/weekly_reports.html", {
        "project": project,
        "reports": reports,
        "next_week_number": next_week_number,
        "can_upload": can_upload,
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

    target_report_type, expected_week_number, target_instance, can_upload = (
        _next_weekly_report(reports)
    )

    if not can_upload:
        messages.warning(
            request,
            "You must wait until the previous report is reviewed by the Guide."
        )
        return redirect("accounts:student_progress")

    # --------------------------------------------------------
    # POST
    # --------------------------------------------------------

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
            progress.marks = None
            progress.detailed_marks = {}

            progress.save()

            report_name = (
                f"Weekly Progress Report - Week {expected_week_number}"
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

    report_name = f"Weekly Progress Report - Week {expected_week_number}"

    return render(
        request,
        "student/progress_form.html",
        {
            "form": form,

            "project": project,

            "report_type": target_report_type,

            "report_name": report_name,

            "next_week_number": expected_week_number,

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
            progress.marks = None
            progress.detailed_marks = {}
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

    projects = _panel_projects_with_final_reports(request.user)
    student_count = User.objects.filter(
        is_student=True,
        is_superuser=False,
    ).count()
    
    pending_count = projects.exclude(
        panel_reviews__panel_member=request.user
    ).distinct().count()
    completed_count = projects.filter(
        panel_reviews__panel_member=request.user
    ).distinct().count()

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
        "projects": _panel_projects_with_final_reports(request.user),
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
        .filter(
            Q(panel_members=request.user)
            | Q(panel_members__isnull=True)
        )
        .select_related("guide")
        .prefetch_related(
            Prefetch(
                "panel_reviews",
                queryset=PanelEvaluation.objects.filter(
                    panel_member=request.user
                ).order_by("review_number"),
                to_attr="panel_review_list",
            )
        )
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
def panel_evaluate(request, project_id, review_number=1):
    if not request.user.is_panel:
        return redirect("accounts:dashboard")

    if review_number not in (1, 2, 3):
        raise Http404
        
    project = get_object_or_404(
        ProjectProposal.objects.select_related(
            "student",
            "guide",
        ).filter(
            Q(panel_members=request.user)
            | Q(panel_members__isnull=True)
        ).distinct(),
        id=project_id,
        progress_reports__report_type="FINAL_REPORT",
    )

    final_report = project.progress_reports.filter(
        report_type="FINAL_REPORT"
    ).order_by("-submitted_at").first()
    if not final_report:
        messages.error(request, "This project does not have a final report yet.")
        return redirect("accounts:panel_dashboard")
        
    evaluation = PanelEvaluation.objects.filter(
        project=project,
        review_number=review_number,
        panel_member=request.user,
    ).first()
    rubric_criteria = list(PanelMarkCriterion.objects.all())

    def review_redirect():
        if review_number == 1:
            return redirect("accounts:panel_evaluate", project_id=project.id)
        return redirect(
            "accounts:panel_evaluate_review",
            project_id=project.id,
            review_number=review_number,
        )
    
    if request.method == "POST":
        feedback = request.POST.get("feedback", "").strip()
        titles = request.POST.getlist("criteria_title[]")
        marks = request.POST.getlist("criteria_mark[]")

        if rubric_criteria and titles != [
            criterion.name for criterion in rubric_criteria
        ]:
            messages.error(
                request,
                "The coordinator's mark fields have changed. Reload the page and enter the marks again.",
            )
            return review_redirect()

        if len(titles) != len(marks):
            messages.error(request, "Each mark category must have a matching mark.")
            return review_redirect()

        if rubric_criteria and any(not mark.strip() for mark in marks):
            messages.error(request, "Enter a mark for every coordinator-defined field.")
            return review_redirect()

        detailed_marks = {}
        total_marks = Decimal("0")
        rubric_max_marks = {
            criterion.name: criterion.max_marks
            for criterion in rubric_criteria
        }

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
                return review_redirect()
            if title in detailed_marks:
                messages.error(request, "Mark category names must be unique.")
                return review_redirect()

            try:
                mark_value = Decimal(mark_text)
            except InvalidOperation:
                messages.error(request, "Enter a valid number for each mark.")
                return review_redirect()

            max_mark = rubric_max_marks.get(title, Decimal("100"))
            if (
                not mark_value.is_finite()
                or mark_value < 0
                or mark_value > max_mark
                or mark_value.as_tuple().exponent < -2
            ):
                messages.error(
                    request,
                    f"{title} must be between 0 and {max_mark} with at most two decimal places.",
                )
                return review_redirect()

            detailed_marks[title] = str(mark_value)
            total_marks += mark_value

        if not detailed_marks:
            messages.error(request, "Add at least one mark category.")
            return review_redirect()

        total_max_marks = (
            sum(rubric_max_marks.values(), Decimal("0"))
            if rubric_criteria
            else Decimal("100")
        )
        if total_marks > total_max_marks:
            messages.error(
                request,
                f"Total marks cannot exceed {total_max_marks}.",
            )
            return review_redirect()

        if not evaluation:
            evaluation = PanelEvaluation(
                project=project,
                review_number=review_number,
                panel_member=request.user,
            )
            
        evaluation.feedback = feedback
        evaluation.detailed_marks = detailed_marks
        evaluation.marks = total_marks
        evaluation.panel_member = request.user
        evaluation.save()

        messages.success(
            request,
            f"Panel Review {review_number} marks saved successfully.",
        )
        return redirect("accounts:panel_dashboard")
    return render(request, "panel/evaluate.html", {
        "project": project,
        "final_report": final_report,
        "evaluation": evaluation,
        "review_number": review_number,
        "review_numbers": (1, 2, 3),
        "rubric_criteria": [
            {
                "name": criterion.name,
                "max_marks": criterion.max_marks,
                "value": (
                    evaluation.detailed_marks.get(criterion.name, "")
                    if evaluation
                    else ""
                ),
            }
            for criterion in rubric_criteria
        ],
        "rubric_total": sum(
            (criterion.max_marks for criterion in rubric_criteria),
            Decimal("0"),
        ),
        "has_rubric": bool(rubric_criteria),
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