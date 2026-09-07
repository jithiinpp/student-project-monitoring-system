from django.urls import path

from . import views


app_name = "coordinator"


urlpatterns = [

    path(
        "",
        views.dashboard,
        name="dashboard"
    ),

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

]