from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from projects.models import ProjectProposal


class ProposalReturnToStudentTests(TestCase):

    def setUp(self):
        self.student = User.objects.create_user(
            username="student1",
            password="Pass123!",
            role="STUDENT",
            first_name="Student",
            last_name="One",
        )
        self.expert = User.objects.create_user(
            username="expert1",
            password="Pass123!",
            role="EXPERT",
            first_name="Expert",
            last_name="One",
        )
        self.proposal = ProjectProposal.objects.create(
            student=self.student,
            project_type="MAIN",
            title="AI Monitoring System",
            domain="Artificial Intelligence",
            technologies="Python, Django",
            abstract="Initial abstract",
            description="Initial description",
            status="CHANGES_REQUESTED",
            domain_expert=self.expert,
            expert_comments="Please include more details and improve scope.",
        )

    def test_student_can_edit_and_resubmit_changes_requested_proposal(self):
        self.client.login(username="student1", password="Pass123!")

        url = reverse("accounts:edit_proposal", args=[self.proposal.id])

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            url,
            {
                "project_type": "MAIN",
                "title": "AI Monitoring System Updated",
                "domain": "Artificial Intelligence",
                "technologies": "Python, Django, OpenCV",
                "abstract": "Updated abstract with clearer scope.",
                "description": "Updated description with the final project plan.",
            },
        )

        self.proposal.refresh_from_db()

        self.assertEqual(self.proposal.status, "SUBMITTED")
        self.assertEqual(self.proposal.expert_comments, "")
        self.assertRedirects(
            response,
            reverse("accounts:proposal_detail", args=[self.proposal.id]),
        )
