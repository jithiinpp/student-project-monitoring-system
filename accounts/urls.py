from django.urls import path

from . import views


app_name = "accounts"


urlpatterns = [

    # ========================================================
    # AUTHENTICATION
    # ========================================================

    path(
        "",
        views.login_view,
        name="home"
    ),

    path(
        "login/",
        views.login_view,
        name="login"
    ),

    path(
        "register/",
        views.register_view,
        name="register"
    ),

    path(
        "logout/",
        views.logout_view,
        name="logout"
    ),

    # ========================================================
    # MAIN DASHBOARD
    # ========================================================

    path(
        "dashboard/",
        views.dashboard_view,
        name="dashboard"
    ),

    # ========================================================
    # STUDENT
    # ========================================================

    path(
        "student/dashboard/",
        views.student_dashboard,
        name="student_dashboard"
    ),

    path(
        "student/proposals/",
        views.student_proposals,
        name="student_proposals"
    ),

    path(
        "student/proposals/add/",
        views.add_proposal,
        name="add_proposal"
    ),

    path(
        "student/proposals/<int:proposal_id>/",
        views.proposal_detail,
        name="proposal_detail"
    ),

    # ========================================================
    # COORDINATOR
    # ========================================================

    path(
        "coordinator/dashboard/",
        views.coordinator_dashboard,
        name="coordinator_dashboard"
    ),

    # ========================================================
    # EXPERT
    # ========================================================

    path(
        "expert/dashboard/",
        views.expert_dashboard,
        name="expert_dashboard"
    ),

    # ========================================================
    # GUIDE
    # ========================================================

    path(
        "guide/dashboard/",
        views.guide_dashboard,
        name="guide_dashboard"
    ),

    # ========================================================
    # PANEL
    # ========================================================

    path(
        "panel/dashboard/",
        views.panel_dashboard,
        name="panel_dashboard"
    ),
]