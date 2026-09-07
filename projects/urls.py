from django.urls import path

from . import views


urlpatterns = [

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

]