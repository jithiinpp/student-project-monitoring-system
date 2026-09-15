from django.urls import path
from . import views


app_name = "experts"


urlpatterns = [

    path(
        "dashboard/",
        views.dashboard,
        name="dashboard"
    ),

    path(
        "proposals/",
        views.my_proposals,
        name="my_proposals"
    ),

    path(
        "proposal/<int:proposal_id>/",
        views.proposal_detail,
        name="proposal_detail"
    ),

    path(
        "proposal/<int:proposal_id>/review/",
        views.review_proposal,
        name="review_proposal"
    ),
]