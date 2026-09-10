from django.urls import path
from . import views


app_name = "guides"


urlpatterns = [

    # Dashboard
    path(
        "dashboard/",
        views.dashboard,
        name="dashboard"
    ),

    # Project detail
    path(
        "project/<int:proposal_id>/",
        views.project_detail,
        name="project_detail"
    ),

    # Reject project
    path(
        "project/<int:proposal_id>/reject/",
        views.reject_project,
        name="reject_project"
    ),

    # Accept / start project
    path(
        "project/<int:proposal_id>/start/",
        views.start_project,
        name="start_project"
    ),
]