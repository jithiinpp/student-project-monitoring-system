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
        "student/schedule/",
        views.student_schedule,
        name="student_schedule"
    ),

    path(
        "student/send-message/<int:project_id>/",
        views.student_send_message,
        name="student_send_message"
    ),

    path(
        "student/discussion/",
        views.student_discussion,
        name="student_discussion"
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

    path(
        "student/profile/<int:student_id>/",
        views.student_profile,
        name="student_profile"
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
        "student/weekly-reports/",
        views.student_weekly_reports,
        name="student_weekly_reports"
    ),

    path(
        "student/final-reports/",
        views.student_final_reports,
        name="student_final_reports"
    ),

    path(
        "student/progress/add/",
        views.add_progress,
        name="add_progress"
    ),

    path(
        "student/progress/final/",
        views.add_final_report,
        name="add_final_report"
    ),


    # =====================================================
    # COORDINATOR
    # =====================================================


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

    path(
        "panel/evaluations/",
        views.panel_evaluations,
        name="panel_evaluations"
    ),

    path(
        "panel/students/",
        views.panel_students,
        name="panel_students"
    ),

    path(
        "panel/schedule/",
        views.panel_schedule,
        name="panel_schedule"
    ),

    path(
        "panel/evaluate/<int:project_id>/",
        views.panel_evaluate,
        name="panel_evaluate"
    ),

    path(
        "panel/send-message/<int:project_id>/",
        views.panel_send_message,
        name="panel_send_message"
    ),


    path(
        "final-mark/",
        views.student_final_mark,
         name="student_final_mark"
    ),
]