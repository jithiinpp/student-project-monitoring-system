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
        "proposals/<int:proposal_id>/send-message/",
        views.coordinator_send_message,
        name="coordinator_send_message"
    ),

    path(
        "proposals/<int:proposal_id>/schedule-review/",
        views.schedule_review,
        name="schedule_review"
    ),

    path(
        "schedule-reviews/",
        views.schedule_reviews_list,
        name="schedule_reviews_list"
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
        "faculty/",
        views.faculty,
        name="faculty"
    ),

    path(
        "faculty/add/",
        views.add_faculty,
        name="add_faculty"
    ),

    path(
        "experts/",
        views.experts,
        name="experts"
    ),

    path(
        "experts/add/",
        views.assign_faculty_role,
        {"role": "is_expert"},
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
        views.assign_faculty_role,
        {"role": "is_guide"},
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
        views.assign_faculty_role,
        {"role": "is_panel"},
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

    # Students
    path(
        "students/",
        views.students,
        name="students"
    ),
]