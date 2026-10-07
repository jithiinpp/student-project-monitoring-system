from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "is_student",
        "is_coordinator",
        "is_expert",
        "is_guide",
        "is_panel",
        "department",
        "is_active",
    )

    list_filter = (
        "is_student",
        "is_coordinator",
        "is_expert",
        "is_guide",
        "is_panel",
        "department",
        "is_active",
    )

    search_fields = (
        "username",
        "first_name",
        "last_name",
        "email",
        "roll_number",
    )

    fieldsets = UserAdmin.fieldsets + (
        (
            "SPMS Information",
            {
                "fields": (
                    "is_student",
                    "is_coordinator",
                    "is_expert",
                    "is_guide",
                    "is_panel",
                    "phone",
                    "roll_number",
                    "department",
                    "domain_of_expertise",
                    "semester",
                    "batch",
                )
            }
        ),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            "SPMS Information",
            {
                "fields": (
                    "is_student",
                    "is_coordinator",
                    "is_expert",
                    "is_guide",
                    "is_panel",
                    "phone",
                    "roll_number",
                    "department",
                    "domain_of_expertise",
                    "semester",
                    "batch",
                )
            }
        ),
    )