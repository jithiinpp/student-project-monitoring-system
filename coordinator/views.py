from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import User
from projects.models import ProjectProposal


# =========================================================
# COORDINATOR ACCESS CHECK
# =========================================================

def coordinator_required(view_func):

    @login_required
    def wrapper(request, *args, **kwargs):

        # Superuser can access Coordinator
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
        role="STUDENT"
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

    context = {
        "student_count": students.count(),

        "expert_count": experts.count(),

        "guide_count": guides.count(),

        "panel_count": panels.count(),

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

    # -----------------------------------------------------
    # ACTIVE DOMAIN EXPERTS
    # -----------------------------------------------------

    experts = User.objects.filter(
        role="EXPERT",
        is_active=True
    ).order_by(
        "first_name",
        "last_name",
        "username"
    )

    # -----------------------------------------------------
    # ACTIVE GUIDES
    # -----------------------------------------------------

    guides = User.objects.filter(
        role="GUIDE",
        is_active=True
    ).order_by(
        "first_name",
        "last_name",
        "username"
    )

    return render(
        request,
        "coordinator/proposal_detail.html",
        {
            "proposal": proposal,
            "experts": experts,
            "guides": guides,
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

    # Only POST is allowed
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

    # -----------------------------------------------------
    # ASSIGN EXPERT
    # -----------------------------------------------------

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

    # Only POST
    if request.method != "POST":

        return redirect(
            "coordinator:proposal_detail",
            proposal_id=proposal.id
        )

    # -----------------------------------------------------
    # EXPERT MUST APPROVE FIRST
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
    # FINAL COORDINATOR APPROVAL
    # -----------------------------------------------------

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
# ASSIGN GUIDE TO APPROVED PROJECT
# =========================================================

@coordinator_required
def assign_guide(request, proposal_id):

    proposal = get_object_or_404(
        ProjectProposal,
        id=proposal_id
    )

    # Only POST
    if request.method != "POST":

        return redirect(
            "coordinator:proposal_detail",
            proposal_id=proposal.id
        )

    # -----------------------------------------------------
    # COORDINATOR MUST APPROVE FIRST
    # -----------------------------------------------------

    if proposal.status != "COORDINATOR_APPROVED":

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

    # -----------------------------------------------------
    # FIND ACTIVE GUIDE
    # -----------------------------------------------------

    guide = get_object_or_404(
        User,
        id=guide_id,
        role="GUIDE",
        is_active=True
    )

    # -----------------------------------------------------
    # ASSIGN GUIDE
    # -----------------------------------------------------

    proposal.guide = guide
    proposal.status = "GUIDE_ASSIGNED"

    proposal.save(
        update_fields=[
            "guide",
            "status",
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

    return render(
        request,
        "coordinator/guide_detail.html",
        {
            "guide": guide
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