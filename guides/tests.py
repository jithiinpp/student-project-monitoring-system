from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from projects.forms import ProjectProgressForm
from projects.models import ProjectProgress, ProjectProposal
from guides.models import GuideEvaluation


class ReportDetailTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.student = user_model.objects.create_user(
            username="student",
            password="password",
            is_student=True,
        )
        self.guide = user_model.objects.create_user(
            username="guide",
            password="password",
            is_guide=True,
        )
        self.project = ProjectProposal.objects.create(
            student=self.student,
            guide=self.guide,
            title="Example project",
        )
        self.report = ProjectProgress.objects.create(
            project=self.project,
            student=self.student,
            report_type="PROGRESS_1",
            title="First progress report",
            description="The student's submitted report content.",
        )
        self.client.force_login(self.guide)

    def test_report_detail_displays_student_report(self):
        response = self.client.get(
            reverse("guides:report_detail", args=[self.report.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "First progress report")
        self.assertContains(response, "Week 1")
        self.assertContains(response, "The student&#x27;s submitted report content.")
        self.assertContains(response, 'name="feedback"')

    def test_final_report_detail_displays_report_without_week_number(self):
        final_report = ProjectProgress.objects.create(
            project=self.project,
            student=self.student,
            report_type="FINAL_REPORT",
            title="Final project report",
            description="Completed project summary.",
        )

        response = self.client.get(
            reverse("guides:report_detail", args=[final_report.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Final project report")
        self.assertContains(response, "Completed project summary.")
        self.assertNotContains(response, "Week 1")

    def test_report_review_saves_feedback(self):
        response = self.client.post(
            reverse("guides:review_progress", args=[self.report.id]),
            {
                "status": "REVIEWED",
                "feedback": "Please add more detail.",
                "criteria_title[]": ["Report quality"],
                "criteria_mark[]": ["12"],
            },
        )

        self.assertRedirects(
            response,
            reverse("guides:report_detail", args=[self.report.id]),
        )
        self.report.refresh_from_db()
        self.assertEqual(self.report.status, "REVIEWED")
        self.assertEqual(self.report.guide_feedback, "Please add more detail.")
        self.assertEqual(self.report.marks, 12)

    def test_guide_can_save_and_update_dynamic_final_mark_categories(self):
        self.report.status = "REVIEWED"
        self.report.save(update_fields=["status"])
        final_report = ProjectProgress.objects.create(
            project=self.project,
            student=self.student,
            report_type="FINAL_REPORT",
            title="Final report",
            description="Completed project summary.",
            status="REVIEWED",
        )
        detail_url = reverse("guides:project_detail", args=[self.project.id])

        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Guide Mark Categories")
        self.assertContains(response, "+ Add Mark Category")
        self.assertContains(response, 'id="guide-mark-total"')

        response = self.client.post(
            reverse("guides:evaluate_project", args=[self.project.id]),
            {
                "criteria_title[]": ["Report Quality", "Presentation"],
                "criteria_mark[]": ["40", "35.5"],
                "feedback": "Strong work.",
            },
        )
        self.assertRedirects(response, detail_url)

        evaluation = GuideEvaluation.objects.get(project=self.project)
        self.assertEqual(evaluation.marks, 75.5)
        self.assertEqual(
            evaluation.detailed_marks,
            {"Report Quality": "40", "Presentation": "35.5"},
        )
        self.assertEqual(evaluation.feedback, "Strong work.")

        response = self.client.post(
            reverse("guides:evaluate_project", args=[self.project.id]),
            {
                "criteria_title[]": ["Presentation"],
                "criteria_mark[]": ["82"],
                "feedback": "Updated mark.",
            },
        )
        self.assertRedirects(response, detail_url)
        evaluation.refresh_from_db()
        self.assertEqual(evaluation.detailed_marks, {"Presentation": "82"})
        self.assertEqual(evaluation.marks, 82)
        final_report.refresh_from_db()
        self.assertEqual(final_report.status, "REVIEWED")

    def test_guide_can_score_weekly_report_with_mark_categories(self):
        self.report.status = "SUBMITTED"
        self.report.save(update_fields=["status"])

        detail_response = self.client.get(
            reverse("guides:project_detail", args=[self.project.id])
        )
        self.assertEqual(detail_response.status_code, 200)
        self.assertContains(detail_response, "Weekly Report Mark Categories")
        self.assertContains(detail_response, "Categories (out of 20)")

        report_detail_response = self.client.get(
            reverse("guides:report_detail", args=[self.report.id])
        )
        self.assertContains(report_detail_response, 'max="20"')
        self.assertContains(report_detail_response, "/ 20")

        response = self.client.post(
            reverse("guides:review_progress", args=[self.report.id]),
            {
                "status": "REVIEWED",
                "feedback": "Good progress.",
                "criteria_title[]": ["Participation", "Documentation"],
                "criteria_mark[]": ["12", "8"],
            },
        )

        self.assertRedirects(
            response,
            reverse("guides:report_detail", args=[self.report.id]),
        )
        self.report.refresh_from_db()
        self.assertEqual(self.report.status, "REVIEWED")
        self.assertEqual(self.report.marks, 20)
        self.assertEqual(
            self.report.detailed_marks,
            {"Participation": "12", "Documentation": "8"},
        )

    def test_guide_marks_are_saved_separately_for_each_weekly_report(self):
        later_report = ProjectProgress.objects.create(
            project=self.project,
            student=self.student,
            report_type="PROGRESS_3",
            week_number=4,
            title="Week 4 report",
            description="Another week's work.",
        )

        for report, mark in ((self.report, "14"), (later_report, "18")):
            response = self.client.post(
                reverse("guides:review_progress", args=[report.id]),
                {
                    "status": "REVIEWED",
                    "criteria_title[]": ["Weekly score"],
                    "criteria_mark[]": [mark],
                },
            )
            self.assertRedirects(
                response,
                reverse("guides:report_detail", args=[report.id]),
            )

        self.report.refresh_from_db()
        later_report.refresh_from_db()
        self.assertEqual(self.report.marks, 14)
        self.assertEqual(later_report.marks, 18)
        self.assertEqual(self.report.week_label, "Week 1")
        self.assertEqual(later_report.week_label, "Week 4")

    def test_weekly_report_marks_cannot_exceed_20_but_final_report_allows_100(self):
        response = self.client.post(
            reverse("guides:review_progress", args=[self.report.id]),
            {
                "status": "REVIEWED",
                "criteria_title[]": ["Weekly score"],
                "criteria_mark[]": ["21"],
            },
        )
        self.assertRedirects(
            response,
            reverse("guides:report_detail", args=[self.report.id]),
        )
        self.report.refresh_from_db()
        self.assertIsNone(self.report.marks)
        self.assertEqual(self.report.status, "SUBMITTED")

        final_report = ProjectProgress.objects.create(
            project=self.project,
            student=self.student,
            report_type="FINAL_REPORT",
            title="Final report",
            description="Completed project summary.",
        )
        response = self.client.post(
            reverse("guides:review_progress", args=[final_report.id]),
            {
                "status": "REVIEWED",
                "criteria_title[]": ["Final score"],
                "criteria_mark[]": ["100"],
            },
        )
        self.assertRedirects(
            response,
            reverse("guides:report_detail", args=[final_report.id]),
        )
        final_report.refresh_from_db()
        self.assertEqual(final_report.marks, 100)

    def test_guide_cannot_approve_report_without_entering_marks(self):
        response = self.client.post(
            reverse("guides:review_progress", args=[self.report.id]),
            {
                "status": "REVIEWED",
                "feedback": "Reviewed without a score.",
                "criteria_title[]": [""],
                "criteria_mark[]": [""],
            },
        )

        self.assertRedirects(
            response,
            reverse("guides:report_detail", args=[self.report.id]),
        )
        self.report.refresh_from_db()
        self.assertEqual(self.report.status, "SUBMITTED")
        self.assertIsNone(self.report.marks)

    def test_requesting_changes_clears_previous_report_marks(self):
        self.report.status = "REVIEWED"
        self.report.marks = 15
        self.report.detailed_marks = {"Quality": "15"}
        self.report.save(
            update_fields=["status", "marks", "detailed_marks"]
        )

        response = self.client.post(
            reverse("guides:review_progress", args=[self.report.id]),
            {
                "status": "CHANGES_REQUIRED",
                "feedback": "Please revise this report.",
            },
        )

        self.assertRedirects(
            response,
            reverse("guides:report_detail", args=[self.report.id]),
        )
        self.report.refresh_from_db()
        self.assertEqual(self.report.status, "CHANGES_REQUIRED")
        self.assertIsNone(self.report.marks)
        self.assertEqual(self.report.detailed_marks, {})

    def test_guide_cannot_save_invalid_or_over_limit_mark_categories(self):
        self.report.status = "REVIEWED"
        self.report.save(update_fields=["status"])
        ProjectProgress.objects.create(
            project=self.project,
            student=self.student,
            report_type="FINAL_REPORT",
            title="Final report",
            description="Completed project summary.",
            status="REVIEWED",
        )
        evaluate_url = reverse("guides:evaluate_project", args=[self.project.id])
        invalid_rows = (
            (["A"], [""]),
            (["A"], ["not-a-mark"]),
            (["A"], ["101"]),
            (["A"], ["10.123"]),
            (["A", "A"], ["20", "30"]),
            (["A", "B"], ["60", "41"]),
        )
        for titles, marks in invalid_rows:
            with self.subTest(titles=titles, marks=marks):
                response = self.client.post(
                    evaluate_url,
                    {
                        "criteria_title[]": titles,
                        "criteria_mark[]": marks,
                        "feedback": "",
                    },
                )
                self.assertRedirects(
                    response,
                    reverse("guides:project_detail", args=[self.project.id]),
                )

        self.assertFalse(GuideEvaluation.objects.filter(project=self.project).exists())


class ProjectProgressFormTests(TestCase):
    def get_form(self, filename, content):
        return ProjectProgressForm(
            data={
                "week_number": "1",
                "title": "Progress report",
                "description": "Work completed this week.",
            },
            files={
                "document": SimpleUploadedFile(filename, content),
            },
            require_week_number=True,
            expected_week_number=1,
        )

    def test_accepts_pdf_supporting_document(self):
        form = self.get_form("supporting-document.pdf", b"%PDF-1.7\nreport")

        self.assertTrue(form.is_valid(), form.errors)

    def test_rejects_non_pdf_supporting_document(self):
        form = self.get_form("supporting-document.docx", b"%PDF-1.7\nreport")

        self.assertFalse(form.is_valid())
        self.assertIn("document", form.errors)

    def test_rejects_file_without_pdf_signature(self):
        form = self.get_form("supporting-document.pdf", b"not a PDF")

        self.assertFalse(form.is_valid())
        self.assertIn("document", form.errors)

    def test_rejects_week_number_that_does_not_match_report_stage(self):
        form = ProjectProgressForm(
            data={
                "week_number": "2",
                "title": "Progress report",
                "description": "Work completed this week.",
            },
            require_week_number=True,
            expected_week_number=1,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("week_number", form.errors)

    def test_accepts_week_numbers_after_week_three(self):
        form = ProjectProgressForm(
            data={
                "week_number": "4",
                "title": "Week 4 report",
                "description": "Work completed this week.",
            },
            require_week_number=True,
            expected_week_number=4,
        )

        self.assertTrue(form.is_valid(), form.errors)


class StudentProgressFormPageTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.student = user_model.objects.create_user(
            username="reporting-student",
            is_student=True,
        )
        self.guide = user_model.objects.create_user(
            username="reporting-guide",
            is_guide=True,
        )
        self.project = ProjectProposal.objects.create(
            student=self.student,
            guide=self.guide,
            title="Hospital management System",
            status="IN_PROGRESS",
        )
        self.client.force_login(self.student)

    def test_weekly_form_shows_week_number_and_pdf_only(self):
        response = self.client.get(reverse("accounts:add_progress"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hospital management System")
        self.assertContains(response, "Week Number")
        self.assertContains(response, 'accept=".pdf,application/pdf"')
        self.assertContains(response, "Optional: PDF only.")

    def test_student_can_upload_week_four_after_week_three_is_reviewed(self):
        for week_number, report_type in (
            (1, "PROGRESS_1"),
            (2, "PROGRESS_2"),
            (3, "PROGRESS_3"),
        ):
            ProjectProgress.objects.create(
                project=self.project,
                student=self.student,
                report_type=report_type,
                week_number=week_number,
                title=f"Week {week_number} report",
                description=f"Work from week {week_number}.",
                status="REVIEWED",
                marks=15,
                detailed_marks={"Weekly score": "15"},
            )

        response = self.client.get(reverse("accounts:add_progress"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["next_week_number"], 4)
        self.assertEqual(response.context["report_type"], "PROGRESS_3")
        self.assertIsNone(response.context["form"].fields["week_number"].max_value)

        response = self.client.post(
            reverse("accounts:add_progress"),
            {
                "week_number": "4",
                "title": "Week 4 report",
                "description": "Work completed during week four.",
            },
        )

        self.assertRedirects(response, reverse("accounts:student_progress"))
        week_four_report = ProjectProgress.objects.get(week_number=4)
        self.assertEqual(week_four_report.report_type, "PROGRESS_3")
        self.assertEqual(week_four_report.status, "SUBMITTED")

    def test_final_report_form_hides_week_number_but_allows_pdf(self):
        response = self.client.get(reverse("accounts:add_final_report"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Upload Final Report")
        self.assertNotContains(response, "Week Number")
        self.assertContains(response, 'accept=".pdf,application/pdf"')
