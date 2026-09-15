from django.urls import path

from . import views


app_name = "guides"


urlpatterns = [

    path(
        "dashboard/",
        views.dashboard,
        name="dashboard"
    ),

    path(
        "students/",
        views.students,
        name="students"
    ),

    path(
        "project/<int:proposal_id>/",
        views.project_detail,
        name="project_detail"
    ),

    path(
        "project/<int:proposal_id>/start/",
        views.start_project,
        name="start_project"
    ),

    path(
        "project/<int:proposal_id>/reject/",
        views.reject_project,
        name="reject_project"
    ),

    path(
        "project/<int:proposal_id>/evaluate/",
        views.evaluate_project,
        name="evaluate_project"
    ),

    path(
        "progress/<int:progress_id>/review/",
        views.review_progress,
        name="review_progress"
    ),
]