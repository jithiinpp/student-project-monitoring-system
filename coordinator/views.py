from django.db.models import Q
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import Http404
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.utils import timezone

from accounts.models import User

from projects.models import (
    ProjectProposal,
    ProposalChangeRequest,
)


# =========================================================
# FINAL APPROVED PROJECT STATUSES
# =========================================================
#
# Once Coordinator gives final approval:
#
# COORDINATOR_APPROVED
#        ↓
# GUIDE_ASSIGNED
#        ↓
# IN_PROGRESS
#        ↓
# COMPLETED
#
# If Guide rejects:
#
# GUIDE_REJECTED
#        ↓
# Coordinator assigns another Guide
#
# All these stages belong to a project that has already
# received Coordinator final approval.
# =========================================================

FINAL_APPROVED_STATUSES = [
    "COORDINATOR_APPROVED",
    "GUIDE_ASSIGNED",
    "GUIDE_REJECTED",
    "IN_PROGRESS",
    "COMPLETED",
]


# =========================================================
# COORDINATOR ACCESS CHECK
# =========================================================

def coordinator_required(view_func):

    @login_required
    def wrapper(request, *args, **kwargs):

        # Superuser = Coordinator
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)

        # Normal Coordinator
        if request.user.is_coordinator:
            return view_func(request, *args, **kwargs)

        messages.error(
            request,
            "You are not authorized to access the Coordinator page."
        )

        return redirect("accounts:dashboard")

    return wrapper


# =========================================================
# COORDINATOR DASHBOARD
# =========================================================

@coordinator_required
def dashboard(request):

    # -----------------------------------------------------
    # STUDENTS
    # -----------------------------------------------------

    students = User.objects.filter(
        is_student=True,
        is_superuser=False
    )

    # -----------------------------------------------------
    # DOMAIN EXPERTS
    # -----------------------------------------------------

    experts = User.objects.filter(
        is_expert=True,
        is_superuser=False
    )

    # -----------------------------------------------------
    # GUIDES
    # -----------------------------------------------------

    guides = User.objects.filter(
        is_guide=True,
        is_superuser=False
    )

    # -----------------------------------------------------
    # PANEL MEMBERS
    # -----------------------------------------------------

    panels = User.objects.filter(
        is_panel=True,
        is_superuser=False
    )

    # -----------------------------------------------------
    # ALL ACTIVE PROPOSALS
    # -----------------------------------------------------

    proposals = ProjectProposal.objects.exclude(
        status="REJECTED"
    )

    # =====================================================
    # FINAL APPROVED PROJECTS
    # =====================================================
    #
    # IMPORTANT:
    #
    # We cannot use only:
    #
    # status="COORDINATOR_APPROVED"
    #
    # because after Guide assignment the status becomes:
    #
    # GUIDE_ASSIGNED
    #
    # and later:
    #
    # IN_PROGRESS
    # COMPLETED
    #
    # Therefore all final-approved stages are included.
    # =====================================================

    final_approved_queryset = (
        ProjectProposal.objects
        .filter(
            status__in=FINAL_APPROVED_STATUSES
        )
        .select_related(
            "student",
            "domain_expert",
            "guide"
        )
        .order_by("-updated_at")
    )

    # -----------------------------------------------------
    # FINAL APPROVED STUDENT COUNT
    #
    # Count unique students.
    # -----------------------------------------------------

    final_approved_count = (
        final_approved_queryset
        .values("student_id")
        .distinct()
        .count()
    )

    # -----------------------------------------------------
    # RECENT FINAL APPROVED PROJECTS
    # -----------------------------------------------------

    recent_final_approved = (
        final_approved_queryset[:5]
    )

    # -----------------------------------------------------
    # CHANGE REQUEST COUNT
    # -----------------------------------------------------

    changes_requested_count = proposals.filter(
        status="CHANGES_REQUESTED"
    ).count()

    # -----------------------------------------------------
    # GUIDE REJECTION COUNT
    # -----------------------------------------------------

    guide_rejected_count = proposals.filter(
        status="GUIDE_REJECTED"
    ).count()

    # =====================================================
    # DASHBOARD CONTEXT
    # =====================================================
    print("DEBUG DASHBOARD COUNTS:")
    print("Experts:", experts.count())
    print("Guides:", guides.count())
    print("Panels:", panels.count())

    context = {

        # -------------------------------------------------
        # COUNTS
        # -------------------------------------------------

        "student_count":
            students.count(),

        "expert_count":
            experts.count(),

        "guide_count":
            guides.count(),

        "panel_count":
            panels.count(),

        "proposal_count":
            proposals.count(),

        # -------------------------------------------------
        # FINAL APPROVED
        # -------------------------------------------------

        "final_approved_count":
            final_approved_count,

        "final_approved_student_count":
            final_approved_count,

        "final_approved_proposals":
            recent_final_approved,

        # -------------------------------------------------
        # PROPOSAL STATUS
        # -------------------------------------------------

        "submitted_count":
            proposals.filter(
                status="SUBMITTED"
            ).count(),

        "expert_assigned_count":
            proposals.filter(
                status="EXPERT_ASSIGNED"
            ).count(),

        "expert_approved_count":
            proposals.filter(
                status="EXPERT_APPROVED"
            ).count(),

        "changes_requested_count":
            changes_requested_count,

        "pending_change_requests_count":
            ProposalChangeRequest.objects.filter(
                status="PENDING"
            ).count(),

        # Count all proposals that have reached final approval stages
        "approved_count":
            proposals.filter(
                status__in=FINAL_APPROVED_STATUSES
            ).count(),

        "guide_assigned_count":
            proposals.filter(
                status="GUIDE_ASSIGNED"
            ).count(),

        "guide_rejected_count":
            guide_rejected_count,

        "in_progress_count":
            proposals.filter(
                status="IN_PROGRESS"
            ).count(),

        "completed_count":
            proposals.filter(
                status="COMPLETED"
            ).count(),

        # -------------------------------------------------
        # RECENT CHANGE REQUESTS
        # -------------------------------------------------

        "recent_change_requests":
            ProposalChangeRequest.objects.filter(
                status="PENDING"
            ).select_related(
                "proposal",
                "proposal__student",
                "expert"
            ).order_by(
                "-created_at"
            )[:5],

        # -------------------------------------------------
        # RECENT GUIDE REJECTIONS
        # -------------------------------------------------

        "recent_guide_rejections":
            proposals.filter(
                status="GUIDE_REJECTED"
            ).select_related(
                "student",
                "guide"
            ).order_by(
                "-guide_rejected_at",
                "-updated_at"
            )[:5],
    }

    return render(
        request,
        "coordinator/dashboard.html",
        context
    )


# =========================================================
# FINAL APPROVED STUDENTS
# =========================================================

@coordinator_required
def final_approved_students(request):

    # -----------------------------------------------------
    # GET ALL FINAL APPROVED PROJECTS
    # -----------------------------------------------------

    approved_projects = (
        ProjectProposal.objects
        .filter(
            status__in=FINAL_APPROVED_STATUSES
        )
        .select_related(
            "student",
            "domain_expert",
            "guide"
        )
        .order_by("-updated_at")
    )

    # -----------------------------------------------------
    # COUNT UNIQUE FINAL APPROVED STUDENTS
    # -----------------------------------------------------

    final_approved_count = (
        approved_projects
        .values("student_id")
        .distinct()
        .count()
    )

    # -----------------------------------------------------
    # PAGE
    # -----------------------------------------------------

    return render(
        request,
        "coordinator/final_approved_students.html",
        {
            "approved_projects":
                approved_projects,

            "final_approved_count":
                final_approved_count,
        }
    )


# =========================================================
# VIEW ALL PROJECT PROPOSALS
# =========================================================

@coordinator_required
def proposals(request):

    proposal_list = (
        ProjectProposal.objects
        .select_related(
            "student",
            "domain_expert",
            "guide"
        )
        .order_by(
            "submitted_at"
        )
    )

    grouped_proposals = []
    seen_students = set()
    
    for proposal in proposal_list:
        if proposal.student not in seen_students:
            grouped_proposals.append({
                "student": proposal.student,
                "proposals": []
            })
            seen_students.add(proposal.student)
        
        for group in grouped_proposals:
            if group["student"] == proposal.student:
                group["proposals"].append(proposal)
                break

    return render(
        request,
        "coordinator/proposals.html",
        {
            "grouped_proposals": grouped_proposals
        }
    )


# =========================================================
# PROPOSAL DETAIL
# =========================================================

@coordinator_required
def proposal_detail(request, proposal_id):

    proposal = get_object_or_404(
        ProjectProposal.objects.select_related(
            "student",
            "domain_expert",
            "guide"
        ),
        id=proposal_id
    )

    # -----------------------------------------------------
    # DOMAIN EXPERTS
    # -----------------------------------------------------

    experts = User.objects.filter(
        is_expert=True,
        is_active=True,
        is_superuser=False
    ).order_by(
        "first_name",
        "last_name",
        "username"
    )

    # -----------------------------------------------------
    # GUIDES
    # -----------------------------------------------------

    guides = User.objects.filter(
        is_guide=True,
        is_active=True,
        is_superuser=False
    ).order_by(
        "first_name",
        "last_name",
        "username"
    )

    # -----------------------------------------------------
    # CHANGE REQUESTS
    # -----------------------------------------------------

    change_requests = (
        ProposalChangeRequest.objects
        .filter(
            proposal=proposal
        )
        .select_related(
            "expert",
            "coordinator"
        )
        .order_by(
            "-created_at"
        )
    )

    project_messages = proposal.messages.select_related("sender").all()

    return render(
        request,
        "coordinator/proposal_detail.html",
        {
            "proposal": proposal,
            "experts": experts,
            "guides": guides,
            "change_requests": change_requests,
            "project_messages": project_messages,
        }
    )

# =========================================================
# COORDINATOR SEND MESSAGE
# =========================================================

@coordinator_required
def coordinator_send_message(request, proposal_id):
    if request.method == "POST":
        proposal = get_object_or_404(ProjectProposal, id=proposal_id)
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
    return redirect("coordinator:proposal_detail", proposal_id=proposal_id)


# =========================================================
# SCHEDULE REVIEWS LIST
# =========================================================

@coordinator_required
def schedule_reviews_list(request):
    from .models import ScheduleDocument
    
    if request.method == "POST":
        if "schedule_doc" in request.FILES:
            doc = request.FILES["schedule_doc"]
            ScheduleDocument.objects.create(document=doc)
            messages.success(request, "Overall schedule document uploaded successfully. It is now visible to all students and panel members.")
            return redirect("coordinator:schedule_reviews_list")
        else:
            messages.error(request, "Please select a document to upload.")
            
    # Fetch projects that are completed and ready for panel review
    proposals = ProjectProposal.objects.filter(status="COMPLETED").order_by('-updated_at')
    
    latest_doc = ScheduleDocument.objects.first()
    
    return render(
        request,
        "coordinator/schedule_reviews.html",
        {
            "proposals": proposals,
            "latest_doc": latest_doc,
        }
    )

# =========================================================
# SCHEDULE REVIEW
# =========================================================

@coordinator_required
def schedule_review(request, proposal_id):
    if request.method == "POST":
        proposal = get_object_or_404(ProjectProposal, id=proposal_id)
        review_date_str = request.POST.get("review_date")
        
        if review_date_str:
            from django.utils.dateparse import parse_datetime
            from django.utils import timezone
            review_date = parse_datetime(review_date_str)
            if review_date:
                if timezone.is_naive(review_date):
                    review_date = timezone.make_aware(review_date)
                    
                proposal.review_date = review_date
                proposal.save(update_fields=["review_date"])
                
                # Send an automated message to the project discussion thread
                from projects.models import ProjectMessage
                formatted_date = timezone.localtime(review_date).strftime("%A, %B %d, %Y at %I:%M %p")
                system_message = f"📢 **System Notification:** The Panel Review for this project has been scheduled for {formatted_date}."
                
                ProjectMessage.objects.create(
                    project=proposal,
                    sender=request.user, # Or maybe a system user, but coordinator is fine
                    message=system_message
                )
                
                messages.success(request, f"Review scheduled for {formatted_date} and notifications sent to the discussion.")
            else:
                messages.error(request, "Invalid date format.")
        else:
            messages.error(request, "Review date is required.")
            
        referer = request.META.get('HTTP_REFERER')
        if referer:
            return redirect(referer)
            
    return redirect("coordinator:schedule_reviews_list")


# =========================================================
# ASSIGN PROJECT TO DOMAIN EXPERT
# =========================================================

@coordinator_required
def assign_expert(request, proposal_id):

    proposal = get_object_or_404(
        ProjectProposal,
        id=proposal_id
    )

    if request.method != "POST":

        return redirect(
            "coordinator:proposal_detail",
            proposal_id=proposal.id
        )

    expert_id = request.POST.get("expert")

    if not expert_id:

        messages.error(
            request,
            "Please select a Domain Expert."
        )

        return redirect(
            "coordinator:proposal_detail",
            proposal_id=proposal.id
        )

    expert = get_object_or_404(
        User,
        id=expert_id,
        is_expert=True,
        is_active=True,
        is_superuser=False
    )

    proposal.domain_expert = expert
    proposal.status = "EXPERT_ASSIGNED"

    proposal.save(
        update_fields=[
            "domain_expert",
            "status",
            "updated_at"
        ]
    )

    messages.success(
        request,
        f"Project assigned to "
        f"{expert.get_full_name() or expert.username}."
    )

    return redirect(
        "coordinator:proposal_detail",
        proposal_id=proposal.id
    )


# =========================================================
# COORDINATOR FINAL APPROVAL
# =========================================================

@coordinator_required
def approve_project(request, proposal_id):

    proposal = get_object_or_404(
        ProjectProposal,
        id=proposal_id
    )

    if request.method != "POST":

        return redirect(
            "coordinator:proposal_detail",
            proposal_id=proposal.id
        )

    # -----------------------------------------------------
    # EXPERT APPROVAL REQUIRED
    # -----------------------------------------------------

    if proposal.status != "EXPERT_APPROVED":

        messages.error(
            request,
            "You can approve this project only after "
            "the Domain Expert approves it."
        )

        return redirect(
            "coordinator:proposal_detail",
            proposal_id=proposal.id
        )

    # -----------------------------------------------------
    # CHECK WHETHER STUDENT ALREADY HAS FINAL PROJECT
    # -----------------------------------------------------

    already_approved = (
        ProjectProposal.objects
        .filter(
            student=proposal.student,
            status__in=FINAL_APPROVED_STATUSES
        )
        .exclude(
            id=proposal.id
        )
        .exists()
    )

    if already_approved:

        messages.error(
            request,
            "This student already has a final approved project."
        )

        return redirect(
            "coordinator:proposal_detail",
            proposal_id=proposal.id
        )

    # -----------------------------------------------------
    # FINAL APPROVAL
    #
    # Selected proposal:
    # COORDINATOR_APPROVED
    #
    # Other proposals:
    # REJECTED
    # -----------------------------------------------------

    with transaction.atomic():

        # Approve selected proposal
        proposal.status = "COORDINATOR_APPROVED"

        proposal.save(
            update_fields=[
                "status",
                "updated_at"
            ]
        )

        # Reject all other proposals of this student
        ProjectProposal.objects.filter(
            student=proposal.student
        ).exclude(
            id=proposal.id
        ).update(
            status="REJECTED"
        )

    messages.success(
        request,
        "Project approved successfully. "
        "All other proposals from this student "
        "have been rejected."
    )

    return redirect(
        "coordinator:proposal_detail",
        proposal_id=proposal.id
    )


# =========================================================
# ASSIGN GUIDE
# =========================================================

@coordinator_required
def assign_guide(request, proposal_id):

    proposal = get_object_or_404(
        ProjectProposal,
        id=proposal_id
    )

    if request.method != "POST":

        return redirect(
            "coordinator:proposal_detail",
            proposal_id=proposal.id
        )

    # -----------------------------------------------------
    # GUIDE CAN BE ASSIGNED ONLY AFTER FINAL APPROVAL
    #
    # GUIDE_REJECTED is also allowed because the project
    # already received Coordinator final approval.
    # -----------------------------------------------------

    if proposal.status not in [
        "COORDINATOR_APPROVED",
        "GUIDE_REJECTED",
        "GUIDE_ASSIGNED",
        "IN_PROGRESS",
    ]:

        messages.error(
            request,
            "Guide can be assigned only after Coordinator final approval."
        )

        return redirect(
            "coordinator:proposal_detail",
            proposal_id=proposal.id
        )

    guide_id = request.POST.get("guide")
    next_url = request.POST.get("next")

    if not guide_id:

        messages.error(
            request,
            "Please select a Guide."
        )

        if next_url:
            return redirect(next_url)

        return redirect(
            "coordinator:proposal_detail",
            proposal_id=proposal.id
        )

    guide = get_object_or_404(
        User,
        id=guide_id,
        is_guide=True,
        is_active=True,
        is_superuser=False
    )

    # -----------------------------------------------------
    # ASSIGN GUIDE
    # -----------------------------------------------------

    proposal.guide = guide
    if proposal.status in ["COORDINATOR_APPROVED", "GUIDE_REJECTED"]:
        proposal.status = "GUIDE_ASSIGNED"

    # Clear previous Guide rejection
    proposal.guide_rejection_reason = ""
    proposal.guide_rejected_at = None

    proposal.save(
        update_fields=[
            "guide",
            "status",
            "guide_rejection_reason",
            "guide_rejected_at",
            "updated_at"
        ]
    )

    messages.success(
        request,
        f"Guide assigned successfully to "
        f"{guide.get_full_name() or guide.username}."
    )

    if next_url:
        return redirect(next_url)

    return redirect(
        "coordinator:proposal_detail",
        proposal_id=proposal.id
    )


# =========================================================
# CHANGE REQUESTS
# EXPERT -> COORDINATOR
# =========================================================

@coordinator_required
def change_requests(request):

    change_request_list = (
        ProposalChangeRequest.objects
        .filter(
            status="PENDING"
        )
        .select_related(
            "proposal",
            "proposal__student",
            "expert"
        )
        .order_by(
            "-created_at"
        )
    )

    return render(
        request,
        "coordinator/change_requests.html",
        {
            "change_requests":
                change_request_list,

            "change_request_count":
                change_request_list.count(),
        }
    )


# =========================================================
# CHANGE REQUEST DETAIL / SEND TO STUDENT
# =========================================================

@coordinator_required
def send_change_request(request, request_id):

    change_request = get_object_or_404(
        ProposalChangeRequest.objects.select_related(
            "proposal",
            "proposal__student",
            "expert"
        ),
        id=request_id
    )

    if change_request.status != "PENDING":

        messages.error(
            request,
            "This change request has already been processed."
        )

        return redirect(
            "coordinator:change_requests"
        )

    if request.method != "POST":

        return render(
            request,
            "coordinator/send_change_request.html",
            {
                "change_request":
                    change_request
            }
        )

    # -----------------------------------------------------
    # SEND CHANGE REQUEST TO STUDENT
    # -----------------------------------------------------

    coordinator_comments = request.POST.get("coordinator_comments", "").strip()

    change_request.coordinator_comments = coordinator_comments
    change_request.status = "SENT_TO_STUDENT"

    change_request.save(
        update_fields=[
            "coordinator_comments",
            "status"
        ]
    )

    # Proposal remains in CHANGES_REQUESTED
    proposal = change_request.proposal

    proposal.status = "CHANGES_REQUESTED"

    proposal.save(
        update_fields=[
            "status",
            "updated_at"
        ]
    )

    messages.success(
        request,
        "Expert change request has been sent to the student."
    )

    return redirect(
        "coordinator:change_requests"
    )


# =========================================================
# FACULTY LIST
# =========================================================
@coordinator_required
def faculty(request):

    faculty_list = User.objects.filter(
        (
            Q(is_faculty=True)
            | Q(is_expert=True)
            | Q(is_guide=True)
            | Q(is_panel=True)
        ),
        is_student=False,
        is_coordinator=False,
        is_superuser=False,
    ).order_by(
        "first_name",
        "last_name",
        "username"
    )

    return render(
        request,
        "coordinator/faculty.html",
        {
            "faculty": faculty_list,
            "faculty_count": faculty_list.count()
        }
    )


@coordinator_required
def add_faculty(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        if not username or not password:
            messages.error(request, "Username and password are required.")
        elif User.objects.filter(username=username).exists():
            messages.error(request, "That username is already in use.")
        else:
            faculty_member = User.objects.create_user(
                username=username,
                password=password,
                first_name=request.POST.get("first_name", "").strip(),
                last_name=request.POST.get("last_name", "").strip(),
                email=request.POST.get("email", "").strip(),
                phone=request.POST.get("phone", "").strip(),
                department=request.POST.get("department", "").strip(),
                is_faculty=True,
            )
            messages.success(
                request,
                f"Faculty member '{faculty_member.get_full_name() or username}' added.",
            )
            return redirect("coordinator:faculty")

    return render(request, "coordinator/add_faculty.html")


def _assign_faculty_role(request, role, role_title, success_url):
    faculty_candidates = User.objects.filter(
        (
            Q(is_faculty=True)
            | Q(is_expert=True)
            | Q(is_guide=True)
            | Q(is_panel=True)
        ),
        is_student=False,
        is_coordinator=False,
        is_superuser=False,
    ).exclude(
        **{role: True}
    ).order_by(
        "first_name",
        "last_name",
        "username",
    )

    if request.method == "POST":
        faculty_id = request.POST.get("faculty_id", "").strip()
        faculty_member = faculty_candidates.filter(pk=faculty_id).first()
        selected_roles = {
            role
            for role in request.POST.getlist("additional_roles")
            if role in {"is_expert", "is_guide", "is_panel"}
        }
        selected_roles.add(role)
        adding_expert = (
            "is_expert" in selected_roles
            and not (faculty_member and faculty_member.is_expert)
        )
        domain_of_expertise = request.POST.get(
            "domain_of_expertise", ""
        ).strip()

        if faculty_member is None:
            messages.error(
                request,
                "Select a faculty member who does not already have this role.",
            )
        elif adding_expert and not domain_of_expertise:
            messages.error(request, "Enter the expert's domain of expertise.")
        else:
            faculty_member.is_faculty = True
            update_fields = {"is_faculty"}
            newly_assigned_roles = []
            role_titles = {
                "is_expert": "Domain Expert",
                "is_guide": "Guide",
                "is_panel": "Panel Member",
            }
            for selected_role in selected_roles:
                if not getattr(faculty_member, selected_role):
                    setattr(faculty_member, selected_role, True)
                    update_fields.add(selected_role)
                    newly_assigned_roles.append(role_titles[selected_role])

            if adding_expert:
                faculty_member.domain_of_expertise = domain_of_expertise
                update_fields.add("domain_of_expertise")
            faculty_member.save(update_fields=list(update_fields))
            messages.success(
                request,
                f"{', '.join(newly_assigned_roles)} role(s) assigned to "
                f"'{faculty_member.get_full_name() or faculty_member.username}'.",
            )
            return redirect(success_url)

    selected_additional_roles = set(
        request.POST.getlist("additional_roles")
    ) if request.method == "POST" else set()
    role_choices = [
        {
            "key": candidate_role,
            "title": candidate_title,
            "primary": candidate_role == role,
            "selected": (
                candidate_role == role
                or candidate_role in selected_additional_roles
            ),
        }
        for candidate_role, candidate_title in (
            ("is_guide", "Guide"),
            ("is_expert", "Expert"),
            ("is_panel", "Panel"),
        )
    ]
    selected_faculty = faculty_candidates.filter(
        pk=request.POST.get("faculty_id", "")
    ).first() if request.method == "POST" else None
    show_expert_domain = role == "is_expert" or (
        "is_expert" in selected_additional_roles
        and not (selected_faculty and selected_faculty.is_expert)
    )

    return render(
        request,
        "coordinator/assign_faculty_role.html",
        {
            "faculty": faculty_candidates,
            "role_title": role_title,
            "role": role,
            "submit_url": {
                "is_expert": "coordinator:add_expert",
                "is_guide": "coordinator:add_guide",
                "is_panel": "coordinator:add_panel",
            }[role],
            "selected_faculty_id": request.POST.get("faculty_id", ""),
            "domain_of_expertise": request.POST.get(
                "domain_of_expertise", ""
            ),
            "role_choices": role_choices,
            "show_expert_domain": show_expert_domain,
        },
    )


@coordinator_required
def assign_faculty_role(request, role):
    role_settings = {
        "is_expert": ("Domain Expert", "coordinator:experts"),
        "is_guide": ("Guide", "coordinator:guides"),
        "is_panel": ("Panel Member", "coordinator:panels"),
    }
    if role not in role_settings:
        raise Http404

    role_title, success_url = role_settings[role]
    return _assign_faculty_role(request, role, role_title, success_url)


# =========================================================
# EXPERT LIST
# =========================================================

@coordinator_required
def experts(request):

    expert_list = User.objects.filter(
        is_expert=True
    ).order_by(
        "first_name",
        "last_name",
        "username"
    )

    return render(
        request,
        "coordinator/experts.html",
        {
            "experts":
                expert_list,

            "expert_count":
                expert_list.count()
        }
    )


# =========================================================
# ADD EXPERT
# =========================================================

@coordinator_required
def add_expert(request):

    if request.method == "POST":

        username = request.POST.get(
            "username",
            ""
        ).strip()

        first_name = request.POST.get(
            "first_name",
            ""
        ).strip()

        last_name = request.POST.get(
            "last_name",
            ""
        ).strip()

        email = request.POST.get(
            "email",
            ""
        ).strip()

        phone = request.POST.get(
            "phone",
            ""
        ).strip()
        
        domain_of_expertise = request.POST.get(
            "domain_of_expertise",
            ""
        ).strip()

        password = request.POST.get(
            "password",
            ""
        )

        if not username or not password:

            messages.error(
                request,
                "Username and password are required."
            )

            return render(
                request,
                "coordinator/add_expert.html"
            )

        existing_user = User.objects.filter(username=username).first()

        if existing_user:
            if existing_user.check_password(password):
                # Check if user already has this role
                if existing_user.is_expert:
                    messages.warning(
                        request,
                        f"User '{existing_user.username}' is already a Domain Expert."
                    )
                    return render(request, "coordinator/add_expert.html")

                existing_user.is_expert = True
                
                # Check for additional roles
                if request.POST.get("is_guide") == "True":
                    existing_user.is_guide = True
                if request.POST.get("is_panel") == "True":
                    existing_user.is_panel = True
                
                if first_name: existing_user.first_name = first_name
                if last_name: existing_user.last_name = last_name
                if email: existing_user.email = email
                if phone: existing_user.phone = phone
                if domain_of_expertise: existing_user.domain_of_expertise = domain_of_expertise
                
                existing_user.save()

                messages.success(
                    request,
                    f"Successfully added Domain Expert role to existing user '{existing_user.username}'."
                )
                return redirect("coordinator:experts")
            else:
                messages.error(
                    request,
                    "Username already exists. If you want to add a role to this existing account, please provide the correct password."
                )
                return render(request, "coordinator/add_expert.html")

        expert = User.objects.create_user(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            domain_of_expertise=domain_of_expertise,
            is_expert=True,
            is_guide=request.POST.get("is_guide") == "True",
            is_panel=request.POST.get("is_panel") == "True"
        )

        messages.success(
            request,
            f"Domain Expert '{expert.username}' created successfully."
        )

        return redirect(
            "coordinator:experts"
        )

    return render(
        request,
        "coordinator/add_expert.html"
    )


# =========================================================
# EXPERT DETAIL
# =========================================================

@coordinator_required
def expert_detail(request, user_id):

    expert = get_object_or_404(
        User,
        id=user_id,
        is_expert=True
    )

    return render(
        request,
        "coordinator/expert_detail.html",
        {
            "expert": expert
        }
    )


# =========================================================
# DELETE EXPERT
# =========================================================

@coordinator_required
def delete_expert(request, user_id):

    expert = get_object_or_404(
        User,
        id=user_id,
        is_expert=True
    )

    if request.method == "POST":

        username = expert.username

        expert.is_expert = False
        expert.is_faculty = True
        expert.save(update_fields=["is_expert", "is_faculty"])

        messages.success(
            request,
            f"Domain Expert role removed from '{username}'."
        )

    return redirect(
        "coordinator:experts"
    )


# =========================================================
# GUIDE LIST
# =========================================================

@coordinator_required
def guides(request):

    guide_list = User.objects.filter(
        is_guide=True
    ).order_by(
        "first_name",
        "last_name",
        "username"
    )

    return render(
        request,
        "coordinator/guides.html",
        {
            "guides":
                guide_list,

            "guide_count":
                guide_list.count()
        }
    )


# =========================================================
# ADD GUIDE
# =========================================================

@coordinator_required
def add_guide(request):

    if request.method == "POST":

        username = request.POST.get(
            "username",
            ""
        ).strip()

        first_name = request.POST.get(
            "first_name",
            ""
        ).strip()

        last_name = request.POST.get(
            "last_name",
            ""
        ).strip()

        email = request.POST.get(
            "email",
            ""
        ).strip()

        phone = request.POST.get(
            "phone",
            ""
        ).strip()

        password = request.POST.get(
            "password",
            ""
        )

        if not username or not password:

            messages.error(
                request,
                "Username and password are required."
            )

            return render(
                request,
                "coordinator/add_guide.html"
            )

        existing_user = User.objects.filter(username=username).first()

        if existing_user:
            if existing_user.check_password(password):
                # Check if user already has this role
                if existing_user.is_guide:
                    messages.warning(
                        request,
                        f"User '{existing_user.username}' is already a Guide."
                    )
                    return render(request, "coordinator/add_guide.html")

                existing_user.is_guide = True
                
                # Check for additional roles
                if request.POST.get("is_expert") == "True":
                    existing_user.is_expert = True
                if request.POST.get("is_panel") == "True":
                    existing_user.is_panel = True
                
                if first_name: existing_user.first_name = first_name
                if last_name: existing_user.last_name = last_name
                if email: existing_user.email = email
                if phone: existing_user.phone = phone
                
                existing_user.save()

                messages.success(
                    request,
                    f"Successfully added Guide role to existing user '{existing_user.username}'."
                )
                return redirect("coordinator:guides")
            else:
                messages.error(
                    request,
                    "Username already exists. If you want to add a role to this existing account, please provide the correct password."
                )
                return render(request, "coordinator/add_guide.html")

        guide = User.objects.create_user(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            is_guide=True,
            is_expert=request.POST.get("is_expert") == "True",
            is_panel=request.POST.get("is_panel") == "True"
        )

        messages.success(
            request,
            f"Guide '{guide.username}' created successfully."
        )

        return redirect(
            "coordinator:guides"
        )

    return render(
        request,
        "coordinator/add_guide.html"
    )


# =========================================================
# GUIDE DETAIL
# =========================================================

@coordinator_required
def guide_detail(request, user_id):

    guide = get_object_or_404(
        User,
        id=user_id,
        is_guide=True
    )

    assigned_projects = (
        ProjectProposal.objects
        .filter(
            guide=guide
        )
        .select_related(
            "student"
        )
        .order_by(
            "-updated_at"
        )
    )

    return render(
        request,
        "coordinator/guide_detail.html",
        {
            "guide": guide,
            "assigned_projects":
                assigned_projects,
        }
    )


# =========================================================
# DELETE GUIDE
# =========================================================

@coordinator_required
def delete_guide(request, user_id):

    guide = get_object_or_404(
        User,
        id=user_id,
        is_guide=True
    )

    if request.method == "POST":

        username = guide.username

        guide.is_guide = False
        guide.is_faculty = True
        guide.save(update_fields=["is_guide", "is_faculty"])

        messages.success(
            request,
            f"Guide role removed from '{username}'."
        )

    return redirect(
        "coordinator:guides"
    )


# =========================================================
# PANEL LIST
# =========================================================

@coordinator_required
def panels(request):

    panel_list = User.objects.filter(
        is_panel=True
    ).order_by(
        "first_name",
        "last_name",
        "username"
    )

    return render(
        request,
        "coordinator/panels.html",
        {
            "panels":
                panel_list,

            "panel_count":
                panel_list.count()
        }
    )


# =========================================================
# ADD PANEL
# =========================================================

@coordinator_required
def add_panel(request):

    if request.method == "POST":

        username = request.POST.get(
            "username",
            ""
        ).strip()

        first_name = request.POST.get(
            "first_name",
            ""
        ).strip()

        last_name = request.POST.get(
            "last_name",
            ""
        ).strip()

        email = request.POST.get(
            "email",
            ""
        ).strip()

        phone = request.POST.get(
            "phone",
            ""
        ).strip()

        password = request.POST.get(
            "password",
            ""
        )

        if not username or not password:

            messages.error(
                request,
                "Username and password are required."
            )

            return render(
                request,
                "coordinator/add_panel.html"
            )

        existing_user = User.objects.filter(username=username).first()

        if existing_user:
            if existing_user.check_password(password):
                # Check if user already has this role
                if existing_user.is_panel:
                    messages.warning(
                        request,
                        f"User '{existing_user.username}' is already a Panel Member."
                    )
                    return render(request, "coordinator/add_panel.html")

                existing_user.is_panel = True
                
                # Check for additional roles
                if request.POST.get("is_expert") == "True":
                    existing_user.is_expert = True
                if request.POST.get("is_guide") == "True":
                    existing_user.is_guide = True
                
                if first_name: existing_user.first_name = first_name
                if last_name: existing_user.last_name = last_name
                if email: existing_user.email = email
                if phone: existing_user.phone = phone
                
                existing_user.save()

                messages.success(
                    request,
                    f"Successfully added Panel Member role to existing user '{existing_user.username}'."
                )
                return redirect("coordinator:panels")
            else:
                messages.error(
                    request,
                    "Username already exists. If you want to add a role to this existing account, please provide the correct password."
                )
                return render(request, "coordinator/add_panel.html")

        panel = User.objects.create_user(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            is_panel=True,
            is_expert=request.POST.get("is_expert") == "True",
            is_guide=request.POST.get("is_guide") == "True"
        )

        messages.success(
            request,
            f"Panel Member '{panel.username}' created successfully."
        )

        return redirect(
            "coordinator:panels"
        )

    return render(
        request,
        "coordinator/add_panel.html"
    )


# =========================================================
# PANEL DETAIL
# =========================================================

@coordinator_required
def panel_detail(request, user_id):

    panel = get_object_or_404(
        User,
        id=user_id,
        is_panel=True
    )

    return render(
        request,
        "coordinator/panel_detail.html",
        {
            "panel": panel
        }
    )


# =========================================================
# DELETE PANEL
# =========================================================

@coordinator_required
def delete_panel(request, user_id):

    panel = get_object_or_404(
        User,
        id=user_id,
        is_panel=True
    )

    if request.method == "POST":

        username = panel.username

        panel.is_panel = False
        panel.is_faculty = True
        panel.save(update_fields=["is_panel", "is_faculty"])

        messages.success(
            request,
            f"Panel Member role removed from '{username}'."
        )

    return redirect(
        "coordinator:panels"
    )


# =========================================================
# ALL STAFF



# =========================================================
# STUDENTS
# =========================================================

@coordinator_required
def students(request):

    students = User.objects.filter(
        is_student=True,
        is_superuser=False
    ).order_by(
        "first_name",
        "last_name",
        "username"
    )

    total_students = students.count()

    return render(
        request,
        "coordinator/students.html",
        {
            "students":
                students,

            "total_students":
                total_students,
        }
    )