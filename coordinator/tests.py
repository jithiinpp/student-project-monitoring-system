from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from projects.models import ProjectProgress, ProjectProposal


class CoordinatorFacultyListTests(TestCase):

    def setUp(self):
        self.coordinator = User.objects.create_user(
            username="coordinator",
            password="test-password",
            is_coordinator=True,
        )
        self.client.force_login(self.coordinator)

    def test_faculty_page_lists_all_faculty_roles_once(self):
        User.objects.create_user(
            username="expert",
            first_name="Alex",
            last_name="Expert",
            is_expert=True,
        )
        User.objects.create_user(
            username="guide",
            first_name="Grace",
            last_name="Guide",
            is_guide=True,
        )
        User.objects.create_user(
            username="panel",
            first_name="Pat",
            last_name="Panel",
            is_panel=True,
        )
        User.objects.create_user(
            username="multi_role",
            first_name="Morgan",
            last_name="Multi",
            is_expert=True,
            is_guide=True,
            is_panel=True,
        )
        User.objects.create_user(username="student", is_student=True)

        response = self.client.get(reverse("coordinator:faculty"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["faculty_count"], 4)
        self.assertContains(response, "Alex Expert")
        self.assertContains(response, "Grace Guide")
        self.assertContains(response, "Pat Panel")
        self.assertContains(response, "Morgan Multi")
        self.assertNotContains(response, "Faculty Roles")
        self.assertNotContains(response, 'class="status-badge bg-orange"')
        self.assertNotContains(response, 'class="status-badge bg-emerald"')
        self.assertNotContains(response, 'class="status-badge bg-purple"')
        self.assertNotContains(response, 'class="status-badge bg-blue"')
        self.assertNotIn(
            "student",
            [member.username for member in response.context["faculty"]],
        )

    def test_faculty_link_is_available_in_coordinator_sidebar(self):
        response = self.client.get(reverse("coordinator:faculty"))

        self.assertContains(
            response,
            f'href="{reverse("coordinator:faculty")}"',
        )

    def test_add_faculty_creates_account_with_saved_details(self):
        response = self.client.post(
            reverse("coordinator:add_faculty"),
            {
                "username": "new_faculty",
                "password": "secure-test-password",
                "first_name": "Taylor",
                "last_name": "Teacher",
                "email": "taylor@example.edu",
                "phone": "555-0110",
                "department": "Computer Science",
            },
        )

        self.assertRedirects(response, reverse("coordinator:faculty"))
        faculty = User.objects.get(username="new_faculty")
        self.assertTrue(faculty.is_faculty)
        self.assertFalse(faculty.is_guide)
        self.assertEqual(faculty.get_full_name(), "Taylor Teacher")
        self.assertEqual(faculty.email, "taylor@example.edu")
        self.assertEqual(faculty.department, "Computer Science")
        self.assertTrue(faculty.check_password("secure-test-password"))

    def test_add_faculty_form_does_not_assign_roles(self):
        response = self.client.post(
            reverse("coordinator:add_faculty"),
            {
                "username": "multi_role_faculty",
                "password": "secure-test-password",
                "first_name": "Morgan",
                "is_guide": "on",
                "is_expert": "on",
                "is_panel": "on",
                "domain_of_expertise": "Health Informatics",
            },
        )

        self.assertRedirects(response, reverse("coordinator:faculty"))
        faculty = User.objects.get(username="multi_role_faculty")
        self.assertTrue(faculty.is_faculty)
        self.assertFalse(faculty.is_guide)
        self.assertFalse(faculty.is_expert)
        self.assertFalse(faculty.is_panel)
        self.assertFalse(faculty.domain_of_expertise)

    def test_add_faculty_form_has_no_role_assignment_controls(self):
        response = self.client.get(reverse("coordinator:add_faculty"))

        self.assertNotContains(response, "Faculty Roles")
        self.assertNotContains(response, 'name="additional_roles"')
        self.assertNotContains(response, 'name="is_guide"')
        self.assertNotContains(response, 'name="is_expert"')
        self.assertNotContains(response, 'name="is_panel"')

    def test_faculty_page_shows_only_add_faculty_action(self):
        response = self.client.get(reverse("coordinator:faculty"))

        self.assertContains(response, reverse("coordinator:add_faculty"))
        self.assertNotContains(response, reverse("coordinator:add_expert"))
        self.assertNotContains(response, reverse("coordinator:add_guide"))
        self.assertNotContains(response, reverse("coordinator:add_panel"))

    def test_faculty_creation_and_role_assignment_pages_load_coordinator_styles(self):
        add_response = self.client.get(reverse("coordinator:add_faculty"))
        assign_response = self.client.get(reverse("coordinator:add_guide"))

        self.assertEqual(add_response.status_code, 200)
        self.assertEqual(assign_response.status_code, 200)
        for response in (add_response, assign_response):
            self.assertContains(response, "css/coordinator_forms.css")
            self.assertContains(response, "css/coordinator_theme.css")
            self.assertContains(response, "coordinator-form-page")
            self.assertContains(response, 'class="premium-sidebar"')

    def test_guide_role_is_assigned_to_existing_faculty(self):
        faculty = User.objects.create_user(
            username="role_faculty",
            first_name="Riley",
            last_name="Faculty",
            department="Medicine",
            email="riley@example.edu",
            is_faculty=True,
            is_expert=True,
        )

        response = self.client.get(reverse("coordinator:add_guide"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Riley Faculty")
        self.assertContains(response, 'data-department="Medicine"')
        self.assertContains(response, 'data-email="riley@example.edu"')
        self.assertNotContains(response, 'name="password"')

        response = self.client.post(
            reverse("coordinator:add_guide"),
            {"faculty_id": str(faculty.pk)},
        )

        self.assertRedirects(response, reverse("coordinator:guides"))
        faculty.refresh_from_db()
        self.assertTrue(faculty.is_faculty)
        self.assertTrue(faculty.is_expert)
        self.assertTrue(faculty.is_guide)
        self.assertEqual(faculty.email, "riley@example.edu")

    def test_guide_assignment_page_can_assign_multiple_roles_at_once(self):
        faculty = User.objects.create_user(
            username="multiple_assignment_faculty",
            is_faculty=True,
        )

        response = self.client.get(reverse("coordinator:add_guide"))
        self.assertContains(response, "Assign Roles")
        self.assertContains(response, 'name="additional_roles" value="is_expert"')
        self.assertContains(response, 'name="additional_roles" value="is_panel"')

        response = self.client.post(
            reverse("coordinator:add_guide"),
            {
                "faculty_id": str(faculty.pk),
                "additional_roles": ["is_expert", "is_panel"],
                "domain_of_expertise": "Health Informatics",
            },
        )

        self.assertRedirects(response, reverse("coordinator:guides"))
        faculty.refresh_from_db()
        self.assertTrue(faculty.is_guide)
        self.assertTrue(faculty.is_expert)
        self.assertTrue(faculty.is_panel)
        self.assertEqual(faculty.domain_of_expertise, "Health Informatics")

    def test_unassigned_faculty_is_in_faculty_list(self):
        User.objects.create_user(
            username="faculty_without_role",
            first_name="Sam",
            last_name="Teacher",
            is_faculty=True,
        )

        response = self.client.get(reverse("coordinator:faculty"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sam Teacher")
        self.assertContains(response, "Add Faculty")
        self.assertContains(response, "Faculty</span>")

    def test_expert_role_requires_domain_and_saves_to_selected_faculty(self):
        faculty = User.objects.create_user(
            username="expert_faculty",
            is_faculty=True,
        )
        add_expert_url = reverse("coordinator:add_expert")

        response = self.client.post(
            add_expert_url,
            {"faculty_id": str(faculty.pk)},
        )
        self.assertEqual(response.status_code, 200)
        faculty.refresh_from_db()
        self.assertFalse(faculty.is_expert)

        response = self.client.post(
            add_expert_url,
            {
                "faculty_id": str(faculty.pk),
                "domain_of_expertise": "Health Informatics",
            },
        )

        self.assertRedirects(response, reverse("coordinator:experts"))
        faculty.refresh_from_db()
        self.assertTrue(faculty.is_expert)
        self.assertEqual(faculty.domain_of_expertise, "Health Informatics")

    def test_removing_role_keeps_faculty_account(self):
        faculty = User.objects.create_user(
            username="removable_guide",
            is_faculty=True,
            is_guide=True,
        )

        response = self.client.post(
            reverse("coordinator:delete_guide", args=[faculty.pk])
        )

        self.assertRedirects(response, reverse("coordinator:guides"))
        faculty.refresh_from_db()
        self.assertFalse(faculty.is_guide)
        self.assertTrue(faculty.is_faculty)


class CoordinatorGuideSuggestionVisibilityTests(TestCase):

    def test_coordinator_project_page_does_not_show_guide_suggestions(self):
        coordinator = User.objects.create_user(
            username="suggestion_coordinator",
            is_coordinator=True,
        )
        student = User.objects.create_user(
            username="suggestion_student",
            is_student=True,
        )
        project = ProjectProposal.objects.create(
            student=student,
            title="Suggestion visibility project",
        )
        ProjectProgress.objects.create(
            project=project,
            student=student,
            report_type="FINAL_REPORT",
            title="Final report",
            description="Student report content.",
            guide_feedback="Guide suggestion only for the student.",
        )
        self.client.force_login(coordinator)

        response = self.client.get(
            reverse("coordinator:proposal_detail", args=[project.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Guide suggestion only for the student.")

# Create your tests here.
