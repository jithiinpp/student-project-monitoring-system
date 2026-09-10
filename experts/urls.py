from django.urls import path

from . import views


app_name = "experts"


urlpatterns = [

    # Dashboard
    path(
        "dashboard/",
        views.dashboard,
        name="dashboard"
    ),

    # My proposals
    path(
        "proposals/",
        views.my_proposals,
        name="my_proposals"
    ),

    # Proposal detail
    path(
        "proposal/<int:proposal_id>/",
        views.proposal_detail,
        name="proposal_detail"
    ),

    # Review
    path(
        "proposal/<int:proposal_id>/review/",
        views.review_proposal,
        name="review_proposal"
    ),
]