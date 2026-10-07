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
            },
        )

        self.assertRedirects(
            response,
            reverse("guides:report_detail", args=[self.report.id]),
        )
        self.report.refresh_from_db()
        self.assertEqual(self.report.status, "REVIEWED")
        self.assertEqual(self.report.guide_feedback, "Please add more detail.")

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

    def test_final_report_form_hides_week_number_but_allows_pdf(self):
        response = self.client.get(reverse("accounts:add_final_report"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Upload Final Report")
        self.assertNotContains(response, "Week Number")
        self.assertContains(response, 'accept=".pdf,application/pdf"')
