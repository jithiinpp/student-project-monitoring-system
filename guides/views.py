from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from projects.models import ProjectProposal


def guide_required(view_func):

    @login_required
    def wrapper(request, *args, **kwargs):

        if request.user.is_superuser:

            messages.error(
                request,
                "Superuser must use the Coordinator dashboard."
            )

            return redirect("accounts:dashboard")

        if request.user.role != "GUIDE":

            messages.error(
                request,
                "You are not authorized to access the Guide page."
            )

            return redirect("accounts:dashboard")

        return view_func(request, *args, **kwargs)

    return wrapper


# =========================================================
# GUIDE DASHBOARD
# =========================================================

@guide_required
def dashboard(request):

    projects = ProjectProposal.objects.filter(
        guide=request.user
    ).select_related(
        "student"
    )

    context = {

        "project_count": projects.count(),

        "active_count": projects.filter(
            status="IN_PROGRESS"
        ).count(),

        "assigned_count": projects.filter(
            status="GUIDE_ASSIGNED"
        ).count(),

        "completed_count": projects.filter(
            status="COMPLETED"
        ).count(),

        "projects": projects.order_by(
            "-updated_at"
        ),
    }

    return render(
        request,
        "guides/dashboard.html",
        context
    )


# =========================================================
# GUIDE'S ASSIGNED STUDENTS
# =========================================================

@guide_required
def students(request):

    projects = ProjectProposal.objects.filter(
        guide=request.user
    ).select_related(
        "student"
    ).order_by(
        "student__first_name",
        "student__last_name"
    )

    return render(
        request,
        "guides/students.html",
        {
            "projects": projects
        }
    )


# =========================================================
# PROJECT DETAIL
# =========================================================

@guide_required
def project_detail(request, proposal_id):

    project = get_object_or_404(
        ProjectProposal.objects.select_related(
            "student",
            "guide",
            "domain_expert"
        ),
        id=proposal_id,
        guide=request.user
    )

    return render(
        request,
        "guides/project_detail.html",
        {
            "project": project
        }
    )