from django.contrib import admin
from django.utils.html import format_html

from university_app.models import UniversityRequest
from admin_app.models import ApprovedUniversityAccount


@admin.register(UniversityRequest)
class UniversityRequestAdmin(admin.ModelAdmin):
    list_display = (
        'college_id',
        'name',
        'approved_university_email',
        'country',
        'state',
        'pincode',
        'contact_number',
        'website_link',
        'status_colored',
        'created_at',
    )

    search_fields = (
        'college_id',
        'name',
        'country',
        'state',
        'pincode',
        'contact_number',
        'approved_account__university_email',  # 🔍 related search
    )

    list_filter = ('status', 'country', 'state', 'created_at')
    ordering = ('-created_at',)
    readonly_fields = ('college_id', 'created_at')
    list_per_page = 20

    # -------------------------------
    # RELATED UNIVERSITY EMAIL
    # -------------------------------
    def approved_university_email(self, obj):
        if hasattr(obj, 'approved_account'):
            return obj.approved_account.university_email
        return "—"

    approved_university_email.short_description = "University Email"

    # -------------------------------
    # WEBSITE LINK
    # -------------------------------
    def website_link(self, obj):
        if obj.website:
            return format_html(
                '<a href="{}" target="_blank" rel="noopener noreferrer">Visit</a>',
                obj.website
            )
        return "—"

    website_link.short_description = "Website"

    # -------------------------------
    # COLORED STATUS
    # -------------------------------
    def status_colored(self, obj):
        colors = {
            'Approved': '#16a34a',   # green
            'Rejected': '#dc2626',   # red
            'Pending': '#ea580c',    # orange
        }
        color = colors.get(obj.status, '#000000')
        return format_html(
            '<strong style="color: {};">{}</strong>',
            color,
            obj.status
        )

    status_colored.short_description = "Status"
