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
        "projects/<int:proposal_id>/",
        views.project_detail,
        name="project_detail"
    ),
]