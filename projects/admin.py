from django.contrib import admin

from .models import ProjectProposal


@admin.register(ProjectProposal)
class ProjectProposalAdmin(admin.ModelAdmin):

    list_display = (
        "title",
        "student",
        "domain",
        "status",
        "submitted_at",
    )

    list_filter = (
        "status",
        "domain",
        "submitted_at",
    )

    search_fields = (
        "title",
        "student__username",
        "student__roll_number",
        "domain",
    )

    readonly_fields = (
        "submitted_at",
        "updated_at",
    )