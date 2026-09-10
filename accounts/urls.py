from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [

    # =====================================================
    # ROOT
    # =====================================================

    path(
        "",
        views.login_view,
        name="home"
    ),


    # =====================================================
    # AUTHENTICATION
    # =====================================================

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


    # =====================================================
    # COMMON DASHBOARD
    # =====================================================

    path(
        "dashboard/",
        views.dashboard_view,
        name="dashboard"
    ),


    # =====================================================
    # STUDENT
    # =====================================================

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

    path(
        "student/proposals/<int:proposal_id>/edit/",
        views.edit_proposal,
        name="edit_proposal"
    ),


    # =====================================================
    # WEEKLY PROGRESS
    # =====================================================

    path(
        "student/progress/",
        views.student_progress,
        name="student_progress"
    ),

    path(
        "student/progress/add/",
        views.add_progress,
        name="add_progress"
    ),


    # =====================================================
    # COORDINATOR
    # =====================================================

    path(
        "coordinator/dashboard/",
        views.coordinator_dashboard,
        name="coordinator_dashboard"
    ),


    # =====================================================
    # DOMAIN EXPERT
    # =====================================================

    path(
        "expert/dashboard/",
        views.expert_dashboard,
        name="expert_dashboard"
    ),


    # =====================================================
    # GUIDE
    # =====================================================

    path(
        "guide/dashboard/",
        views.guide_dashboard,
        name="guide_dashboard"
    ),

    path(
        "guide/students/",
        views.guide_students,
        name="guide_students"
    ),


    # =====================================================
    # PANEL
    # =====================================================

    path(
        "panel/dashboard/",
        views.panel_dashboard,
        name="panel_dashboard"
    ),
]