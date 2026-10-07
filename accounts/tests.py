from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from guides.models import GuideEvaluation
from projects.models import PanelEvaluation, ProjectProgress, ProjectProposal


class AuthenticationPageThemeAndNotificationTests(TestCase):

    def test_login_page_uses_indigo_theme_and_single_notification(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "missing-user", "password": "invalid"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "background: #4f5bd5")
        self.assertContains(response, "background: #edf2f9")
        self.assertContains(response, 'class="notification error" role="alert"')
        self.assertContains(response, "position: fixed")
        self.assertContains(response, "width: min(340px")
        self.assertNotContains(response, "Action needed")
        self.assertContains(response, 'aria-label="Dismiss notification"')
        self.assertEqual(
            response.content.decode().count("Invalid username or password."),
            1,
        )
        self.assertNotContains(response, "logoutPopup")

    def test_logout_shows_one_shared_success_notification(self):
        user = User.objects.create_user(username="logout-user", password="test-password")
        self.client.force_login(user)

        response = self.client.get(reverse("accounts:logout"))

        self.assertRedirects(response, reverse("accounts:login"), fetch_redirect_response=False)
        response = self.client.get(response.url)

        self.assertContains(response, 'class="notification success" role="status"')
        self.assertContains(response, "You have been logged out successfully.")
        self.assertContains(response, "aria-label=\"Dismiss notification\"")
        self.assertEqual(
            response.content.decode().count("You have been logged out successfully."),
            1,
        )

    def test_registration_page_uses_indigo_theme_and_shared_notifications(self):
        response = self.client.get(reverse("accounts:register"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "background: #4f5bd5")
        self.assertContains(response, "background: #edf2f9")
        self.assertNotContains(response, "class=\"auth-messages\"")


class ProposalReturnToStudentTests(TestCase):

    def setUp(self):
        self.student = User.objects.create_user(
            username="student1",
            password="Pass123!",
            is_student=True,
            first_name="Student",
            last_name="One",
        )
        self.expert = User.objects.create_user(
            username="expert1",
            password="Pass123!",
            is_expert=True,
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


class PanelFinalReportTests(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(
            username="panel_student",
            is_student=True,
            first_name="Panel",
            last_name="Student",
            email="panel.student@example.com",
            department="Health Informatics",
            roll_number="HMS-2026-014",
            batch="2026",
            semester="6",
            phone="555-0104",
        )
        self.panel_member = User.objects.create_user(
            username="panel_member",
            is_panel=True,
        )
        self.project = ProjectProposal.objects.create(
            student=self.student,
            title="Hospital management system",
            status="COMPLETED",
        )
        self.final_report = ProjectProgress.objects.create(
            project=self.project,
            student=self.student,
            report_type="FINAL_REPORT",
            title="Hospital system final report",
            description="Final report submitted by the student.",
        )
        self.client.force_login(self.panel_member)

    def test_dashboard_lists_real_final_report_projects(self):
        response = self.client.get(reverse("accounts:panel_dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hospital management system")
        self.assertContains(response, "Panel Student")
        self.assertContains(response, "Health Informatics")
        self.assertContains(response, "HMS-2026-014")
        self.assertContains(response, "Final reports")
        self.assertContains(response, "Pending marks")
        self.assertContains(response, "Total students")
        self.assertContains(response, "href=\"{}\"".format(
            reverse("accounts:panel_students")
        ))
        self.assertContains(
            response,
            reverse("accounts:panel_evaluate", args=[self.project.id]),
        )

    def test_dashboard_shows_mark_status_without_exposing_numeric_score(self):
        PanelEvaluation.objects.create(
            project=self.project,
            panel_member=self.panel_member,
            marks=76,
        )

        response = self.client.get(reverse("accounts:panel_dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Marks entered")
        self.assertContains(response, "Health Informatics")
        self.assertContains(response, "HMS-2026-014")
        self.assertNotContains(response, "Marked: 76")
        self.assertNotContains(response, ">76<")

    def test_panel_students_list_links_student_to_final_report(self):
        User.objects.create_user(
            username="no_project_student",
            first_name="No Project",
            last_name="Student",
            is_student=True,
        )
        response = self.client.get(reverse("accounts:panel_students"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["student_count"], 2)
        self.assertContains(response, "Panel Student")
        self.assertContains(response, "No Project Student")
        self.assertContains(response, "Total Students")
        self.assertContains(response, "Department")
        self.assertContains(response, "Register Number")
        self.assertContains(response, "More details")
        self.assertContains(response, "Email")
        self.assertContains(response, "panel.student@example.com")
        self.assertContains(response, "Batch")
        self.assertContains(response, "2026")
        self.assertContains(response, "Semester")
        self.assertContains(response, "555-0104")
        self.assertContains(response, "View Final Report")
        self.assertContains(response, "Final report: Submitted")
        self.assertContains(response, "nav-text\">Students</span>")
        self.assertContains(
            response,
            reverse("accounts:panel_evaluate", args=[self.project.id]),
        )

    def test_panel_evaluations_show_student_report_status_without_filter_tabs(self):
        response = self.client.get(
            reverse("accounts:panel_evaluations") + "?filter=pending"
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Student Final Reports")
        self.assertContains(response, "Guide report status: Submitted")
        self.assertNotContains(response, "All Projects")
        self.assertNotContains(response, "Pending Reviews")
        self.assertNotContains(response, "Completed</a>")

    def test_panel_evaluations_show_student_first_and_hide_numeric_marks(self):
        PanelEvaluation.objects.create(
            project=self.project,
            panel_member=self.panel_member,
            marks=76,
        )

        response = self.client.get(reverse("accounts:panel_evaluations"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Panel marks entered")
        self.assertContains(response, "Guide report status: Submitted")
        self.assertNotContains(response, "76.00")
        content = response.content.decode()
        self.assertLess(content.index(">Student</th>"), content.index(">Project Title</th>"))

    def test_panel_can_view_final_report_and_save_dynamic_marks(self):
        self.final_report.guide_feedback = "Private guide suggestion for student."
        self.final_report.save(update_fields=["guide_feedback"])
        detail_url = reverse("accounts:panel_evaluate", args=[self.project.id])
        response = self.client.get(detail_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hospital system final report")
        self.assertContains(response, "Final report submitted by the student.")
        self.assertNotContains(response, "Private guide suggestion for student.")
        self.assertNotContains(response, ">Domain</p>")
        self.assertContains(response, "+ Add Mark Category")
        self.assertContains(response, 'id="panel-mark-total"')
        self.assertContains(response, 'aria-label="Mark value"')
        self.assertContains(response, 'class="panel-remove-mark"')
        self.assertNotContains(response, "Project Discussion")
        self.assertNotContains(response, "Communicate with the student")

        response = self.client.post(
            detail_url,
            {
                "criteria_title[]": ["Report quality", "Presentation"],
                "criteria_mark[]": ["40", "35.5"],
                "feedback": "Strong final project.",
            },
        )

        self.assertRedirects(response, reverse("accounts:panel_dashboard"))
        evaluation = PanelEvaluation.objects.get(project=self.project)
        self.assertEqual(evaluation.marks, 75.5)
        self.assertEqual(
            evaluation.detailed_marks,
            {"Report quality": "40", "Presentation": "35.5"},
        )
        self.assertEqual(evaluation.feedback, "Strong final project.")
        self.final_report.refresh_from_db()
        self.assertIsNone(self.final_report.marks)

    def test_panel_can_update_and_remove_mark_categories(self):
        PanelEvaluation.objects.create(
            project=self.project,
            panel_member=self.panel_member,
            marks=30,
            detailed_marks={"Keep": "10", "Remove": "20"},
        )

        response = self.client.get(
            reverse("accounts:panel_evaluate", args=[self.project.id])
        )
        self.assertContains(response, 'value="Keep"')
        self.assertContains(response, 'value="Remove"')

        response = self.client.post(
            reverse("accounts:panel_evaluate", args=[self.project.id]),
            {
                "criteria_title[]": ["Keep"],
                "criteria_mark[]": ["82"],
                "feedback": "",
            },
        )

        self.assertRedirects(response, reverse("accounts:panel_dashboard"))
        evaluation = PanelEvaluation.objects.get(project=self.project)
        self.assertEqual(evaluation.detailed_marks, {"Keep": "82"})
        self.assertEqual(evaluation.marks, 82)

    def test_panel_cannot_submit_marks_over_100(self):
        response = self.client.post(
            reverse("accounts:panel_evaluate", args=[self.project.id]),
            {
                "criteria_title[]": ["A", "B"],
                "criteria_mark[]": ["60", "41"],
                "feedback": "",
            },
        )

        self.assertRedirects(
            response,
            reverse("accounts:panel_evaluate", args=[self.project.id]),
        )
        self.assertFalse(
            PanelEvaluation.objects.filter(project=self.project).exists()
        )

    def test_panel_requires_valid_category_marks(self):
        invalid_rows = (
            (["A"], [""]),
            (["A"], ["abc"]),
            (["A"], ["-1"]),
            (["A"], ["75.555"]),
            ([""], ["10"]),
        )
        for titles, marks in invalid_rows:
            with self.subTest(titles=titles, marks=marks):
                response = self.client.post(
                    reverse("accounts:panel_evaluate", args=[self.project.id]),
                    {
                        "criteria_title[]": titles,
                        "criteria_mark[]": marks,
                        "feedback": "",
                    },
                )
                self.assertRedirects(
                    response,
                    reverse("accounts:panel_evaluate", args=[self.project.id]),
                )

        self.assertFalse(
            PanelEvaluation.objects.filter(project=self.project).exists()
        )

    def test_panel_cannot_evaluate_project_without_final_report(self):
        project_without_final = ProjectProposal.objects.create(
            student=self.student,
            title="Project without final report",
        )

        response = self.client.get(
            reverse("accounts:panel_evaluate", args=[project_without_final.id])
        )

        self.assertEqual(response.status_code, 404)

    def test_student_final_mark_page_shows_guide_and_panel_breakdowns(self):
        guide = User.objects.create_user(
            username="final_mark_guide",
            is_guide=True,
            first_name="Guide",
            last_name="Member",
        )
        GuideEvaluation.objects.create(
            project=self.project,
            guide=guide,
            marks=75,
            detailed_marks={"Report quality": "40", "Presentation": "35"},
        )
        PanelEvaluation.objects.create(
            project=self.project,
            panel_member=self.panel_member,
            marks=82,
            detailed_marks={"Documentation": "42", "Presentation": "40"},
        )
        self.client.force_login(self.student)

        response = self.client.get(reverse("accounts:student_final_mark"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Guide Mark Breakdown")
        self.assertContains(response, "Report quality")
        self.assertContains(response, "Guide Total")
        self.assertContains(response, "75.00 / 100")
        self.assertContains(response, "Panel Mark Breakdown")
        self.assertContains(response, "Documentation")
        self.assertContains(response, "Panel Total")
        self.assertContains(response, "82.00 / 100")

        GuideEvaluation.objects.filter(project=self.project).delete()
        response = self.client.get(reverse("accounts:student_final_mark"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Panel Mark Breakdown")
        self.assertNotContains(response, "Guide Mark Breakdown")

    def test_student_report_pages_display_guide_suggestions(self):
        self.final_report.guide_feedback = "Final report guide suggestion."
        self.final_report.save(update_fields=["guide_feedback"])
        ProjectProgress.objects.create(
            project=self.project,
            student=self.student,
            report_type="PROGRESS_1",
            week_number=1,
            title="Week 1 progress",
            description="Progress update.",
            guide_feedback="Weekly report guide suggestion.",
        )
        self.client.force_login(self.student)

        weekly_response = self.client.get(
            reverse("accounts:student_weekly_reports")
        )
        final_response = self.client.get(
            reverse("accounts:student_final_reports")
        )

        self.assertEqual(weekly_response.status_code, 200)
        self.assertContains(weekly_response, "Weekly report guide suggestion.")
        self.assertEqual(final_response.status_code, 200)
        self.assertContains(final_response, "Final report guide suggestion.")
