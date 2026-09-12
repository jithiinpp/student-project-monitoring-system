from django.urls import path
from . import views


app_name = "coordinator"


urlpatterns = [

    path(
        "dashboard/",
        views.dashboard,
        name="dashboard"
    ),

    # Final approved students
    path(
        "final-approved-students/",
        views.final_approved_students,
        name="final_approved_students"
    ),

    # Proposals
    path(
        "proposals/",
        views.proposals,
        name="proposals"
    ),

    path(
        "proposals/<int:proposal_id>/",
        views.proposal_detail,
        name="proposal_detail"
    ),

    path(
        "proposals/<int:proposal_id>/assign-expert/",
        views.assign_expert,
        name="assign_expert"
    ),

    path(
        "proposals/<int:proposal_id>/approve/",
        views.approve_project,
        name="approve_project"
    ),

    path(
        "proposals/<int:proposal_id>/assign-guide/",
        views.assign_guide,
        name="assign_guide"
    ),

    # Change requests
    path(
        "change-requests/",
        views.change_requests,
        name="change_requests"
    ),

    path(
        "change-requests/<int:request_id>/send/",
        views.send_change_request,
        name="send_change_request"
    ),

    # Experts
    path(
        "experts/",
        views.experts,
        name="experts"
    ),

    path(
        "experts/add/",
        views.add_expert,
        name="add_expert"
    ),

    path(
        "experts/<int:user_id>/",
        views.expert_detail,
        name="expert_detail"
    ),

    path(
        "experts/<int:user_id>/delete/",
        views.delete_expert,
        name="delete_expert"
    ),

    # Guides
    path(
        "guides/",
        views.guides,
        name="guides"
    ),

    path(
        "guides/add/",
        views.add_guide,
        name="add_guide"
    ),

    path(
        "guides/<int:user_id>/",
        views.guide_detail,
        name="guide_detail"
    ),

    path(
        "guides/<int:user_id>/delete/",
        views.delete_guide,
        name="delete_guide"
    ),

    # Panels
    path(
        "panels/",
        views.panels,
        name="panels"
    ),

    path(
        "panels/add/",
        views.add_panel,
        name="add_panel"
    ),

    path(
        "panels/<int:user_id>/",
        views.panel_detail,
        name="panel_detail"
    ),

    path(
        "panels/<int:user_id>/delete/",
        views.delete_panel,
        name="delete_panel"
    ),

    # Staff
    path(
        "staff/",
        views.staff,
        name="staff"
    ),

    path(
        "staff/add/",
        views.add_staff,
        name="add_staff"
    ),

    path(
        "staff/<int:user_id>/",
        views.staff_detail,
        name="staff_detail"
    ),

    path(
        "staff/<int:user_id>/delete/",
        views.delete_staff,
        name="delete_staff"
    ),

    # Students
    path(
        "students/",
        views.students,
        name="students"
    ),
]