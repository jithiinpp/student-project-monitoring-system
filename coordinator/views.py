from django.contrib import messages
from django.contrib.auth.decorators import login_required
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
# COORDINATOR ACCESS CHECK
# =========================================================

def coordinator_required(view_func):

    @login_required
    def wrapper(request, *args, **kwargs):

        # Superuser = Coordinator
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)

        # Normal Coordinator
        if request.user.role == "COORDINATOR":
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

    students = User.objects.filter(
        role="STUDENT",
        is_superuser=False
    )

    experts = User.objects.filter(
        role="EXPERT"
    )

    guides = User.objects.filter(
        role="GUIDE"
    )

    panels = User.objects.filter(
        role="PANEL"
    )

    proposals = ProjectProposal.objects.all()

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

        "approved_count":
            proposals.filter(
                status="COORDINATOR_APPROVED"
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
        .all()
        .order_by("-submitted_at")
    )

    return render(
        request,
        "coordinator/proposals.html",
        {
            "proposals": proposal_list
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

    experts = User.objects.filter(
        role="EXPERT",
        is_active=True
    ).order_by(
        "first_name",
        "last_name",
        "username"
    )

    guides = User.objects.filter(
        role="GUIDE",
        is_active=True
    ).order_by(
        "first_name",
        "last_name",
        "username"
    )

    # All change requests for this proposal
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

    return render(
        request,
        "coordinator/proposal_detail.html",
        {
            "proposal": proposal,
            "experts": experts,
            "guides": guides,
            "change_requests": change_requests,
        }
    )


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
        role="EXPERT",
        is_active=True
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

    # Expert approval is required first
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

    proposal.status = "COORDINATOR_APPROVED"

    proposal.save(
        update_fields=[
            "status",
            "updated_at"
        ]
    )

    messages.success(
        request,
        "Project has been finally approved by the Coordinator."
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

    # Guide can be assigned after final approval
    # OR after a Guide rejected the previous assignment
    if proposal.status not in [
        "COORDINATOR_APPROVED",
        "GUIDE_REJECTED",
    ]:

        messages.error(
            request,
            "Guide can be assigned only after "
            "Coordinator final approval."
        )

        return redirect(
            "coordinator:proposal_detail",
            proposal_id=proposal.id
        )

    guide_id = request.POST.get("guide")

    if not guide_id:

        messages.error(
            request,
            "Please select a Guide."
        )

        return redirect(
            "coordinator:proposal_detail",
            proposal_id=proposal.id
        )

    guide = get_object_or_404(
        User,
        id=guide_id,
        role="GUIDE",
        is_active=True
    )

    proposal.guide = guide
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
            "change_requests": change_request_list,
            "change_request_count": change_request_list.count(),
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

    # Only pending requests can be sent
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
                "change_request": change_request
            }
        )

    # -----------------------------------------------------
    # SEND CHANGE REQUEST TO STUDENT
    # -----------------------------------------------------

    change_request.coordinator = request.user

    change_request.status = "SENT_TO_STUDENT"

    change_request.sent_to_student_at = timezone.now()

    change_request.save(
        update_fields=[
            "coordinator",
            "status",
            "sent_to_student_at"
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
# EXPERT LIST
# =========================================================

@coordinator_required
def experts(request):

    expert_list = User.objects.filter(
        role="EXPERT"
    ).order_by(
        "first_name",
        "last_name",
        "username"
    )

    return render(
        request,
        "coordinator/experts.html",
        {
            "experts": expert_list,
            "expert_count": expert_list.count()
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

        if User.objects.filter(
            username=username
        ).exists():

            messages.error(
                request,
                "Username already exists."
            )

            return render(
                request,
                "coordinator/add_expert.html"
            )

        expert = User.objects.create_user(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            role="EXPERT"
        )

        messages.success(
            request,
            f"Domain Expert '{expert.username}' "
            f"created successfully."
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
        role="EXPERT"
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
        role="EXPERT"
    )

    if request.method == "POST":

        username = expert.username

        expert.delete()

        messages.success(
            request,
            f"Domain Expert '{username}' "
            f"deleted successfully."
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
        role="GUIDE"
    ).order_by(
        "first_name",
        "last_name",
        "username"
    )

    return render(
        request,
        "coordinator/guides.html",
        {
            "guides": guide_list,
            "guide_count": guide_list.count()
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

        if User.objects.filter(
            username=username
        ).exists():

            messages.error(
                request,
                "Username already exists."
            )

            return render(
                request,
                "coordinator/add_guide.html"
            )

        guide = User.objects.create_user(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            role="GUIDE"
        )

        messages.success(
            request,
            f"Guide '{guide.username}' "
            f"created successfully."
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
        role="GUIDE"
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
            "assigned_projects": assigned_projects,
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
        role="GUIDE"
    )

    if request.method == "POST":

        username = guide.username

        guide.delete()

        messages.success(
            request,
            f"Guide '{username}' deleted successfully."
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
        role="PANEL"
    ).order_by(
        "first_name",
        "last_name",
        "username"
    )

    return render(
        request,
        "coordinator/panels.html",
        {
            "panels": panel_list,
            "panel_count": panel_list.count()
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

        if User.objects.filter(
            username=username
        ).exists():

            messages.error(
                request,
                "Username already exists."
            )

            return render(
                request,
                "coordinator/add_panel.html"
            )

        panel = User.objects.create_user(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            role="PANEL"
        )

        messages.success(
            request,
            f"Panel Member '{panel.username}' "
            f"created successfully."
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
        role="PANEL"
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
        role="PANEL"
    )

    if request.method == "POST":

        username = panel.username

        panel.delete()

        messages.success(
            request,
            f"Panel Member '{username}' "
            f"deleted successfully."
        )

    return redirect(
        "coordinator:panels"
    )


# =========================================================
# ALL STAFF
# =========================================================

@coordinator_required
def staff(request):

    staff_list = User.objects.filter(
        role__in=[
            "EXPERT",
            "GUIDE",
            "PANEL"
        ]
    ).order_by(
        "role",
        "first_name",
        "last_name",
        "username"
    )

    return render(
        request,
        "coordinator/staff.html",
        {
            "staff": staff_list
        }
    )


# =========================================================
# ADD STAFF
# =========================================================

@coordinator_required
def add_staff(request):

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

        role = request.POST.get(
            "role",
            ""
        )

        allowed_roles = [
            "EXPERT",
            "GUIDE",
            "PANEL"
        ]

        if not username:

            messages.error(
                request,
                "Username is required."
            )

            return render(
                request,
                "coordinator/add_staff.html"
            )

        if not password:

            messages.error(
                request,
                "Password is required."
            )

            return render(
                request,
                "coordinator/add_staff.html"
            )

        if role not in allowed_roles:

            messages.error(
                request,
                "Please select a valid staff role."
            )

            return render(
                request,
                "coordinator/add_staff.html"
            )

        if User.objects.filter(
            username=username
        ).exists():

            messages.error(
                request,
                "Username already exists."
            )

            return render(
                request,
                "coordinator/add_staff.html"
            )

        staff_member = User.objects.create_user(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            role=role
        )

        role_names = {
            "EXPERT": "Domain Expert",
            "GUIDE": "Guide",
            "PANEL": "Panel Member"
        }

        messages.success(
            request,
            f"{role_names[role]} "
            f"'{staff_member.username}' "
            f"created successfully."
        )

        return redirect(
            "coordinator:staff"
        )

    return render(
        request,
        "coordinator/add_staff.html"
    )


# =========================================================
# STAFF DETAIL
# =========================================================

@coordinator_required
def staff_detail(request, user_id):

    staff_member = get_object_or_404(
        User,
        id=user_id,
        role__in=[
            "EXPERT",
            "GUIDE",
            "PANEL"
        ]
    )

    return render(
        request,
        "coordinator/staff_detail.html",
        {
            "staff_member": staff_member
        }
    )


# =========================================================
# DELETE STAFF
# =========================================================

@coordinator_required
def delete_staff(request, user_id):

    staff_member = get_object_or_404(
        User,
        id=user_id,
        role__in=[
            "EXPERT",
            "GUIDE",
            "PANEL"
        ]
    )

    if request.method == "POST":

        username = staff_member.username

        staff_member.delete()

        messages.success(
            request,
            f"Staff member '{username}' "
            f"deleted successfully."
        )

    return redirect(
        "coordinator:staff"
    )


# =========================================================
# STUDENTS
# =========================================================

@coordinator_required
def students(request):

    students = User.objects.filter(
        role="STUDENT",
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
            "students": students,
            "total_students": total_students,
        }
    )