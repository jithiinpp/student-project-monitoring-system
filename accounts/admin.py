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
        "role",
        "department",
        "is_active",
    )

    list_filter = (
        "role",
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
                    "role",
                    "phone",
                    "roll_number",
                    "department",
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
                    "role",
                    "phone",
                    "roll_number",
                    "department",
                    "semester",
                    "batch",
                )
            }
        ),
    )