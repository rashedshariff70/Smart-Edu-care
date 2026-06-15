from django.contrib import admin
from django.utils.html import format_html

# ---------------------------------------------
# MODELS FROM admin_app
# ---------------------------------------------
from admin_app.models import (
    ApprovedUniversityAccount,
    ApprovedUniversityCredential,
)

# ---------------------------------------------
# MODEL FROM student_app  ✅ FIX HERE
# ---------------------------------------------
from student_app.models import student_login_valid


# =====================================================
# APPROVED UNIVERSITY ACCOUNT
# =====================================================
@admin.register(ApprovedUniversityAccount)
class ApprovedUniversityAccountAdmin(admin.ModelAdmin):
    list_display = (
        "college_id",
        "name",
        "university_email",
        "country",
        "state",
        "pincode",
        "contact_number",
        "website_link",
        "user_link",
        "approved_at",
    )

    search_fields = (
        "college_id",
        "name",
        "university_email",
        "country",
        "state",
        "pincode",
        "contact_number",
        "user__username",
        "user__email",
    )

    list_filter = (
        "country",
        "state",
        "approved_at",
    )

    ordering = ("-approved_at",)
    readonly_fields = ("college_id", "approved_at")
    list_per_page = 20

    # ----------------------------------
    # WEBSITE LINK
    # ----------------------------------
    def website_link(self, obj):
        if obj.website:
            return format_html(
                '<a href="{}" target="_blank" rel="noopener noreferrer">Visit</a>',
                obj.website
            )
        return "—"

    website_link.short_description = "Website"

    # ----------------------------------
    # USER LINK
    # ----------------------------------
    def user_link(self, obj):
        if obj.user:
            return format_html(
                '<a href="/admin/auth/user/{}/change/">{}</a>',
                obj.user.id,
                obj.user.username
            )
        return "—"

    user_link.short_description = "Login User"

    fieldsets = (
        (
            "University Information",
            {
                "fields": (
                    "college_id",
                    "name",
                    "university_email",
                    "contact_number",
                    "website",
                )
            },
        ),
        (
            "Location",
            {
                "fields": (
                    "country",
                    "state",
                    "pincode",
                )
            },
        ),
        (
            "System",
            {
                "fields": (
                    "user",
                    "approved_at",
                )
            },
        ),
    )


# =====================================================
# APPROVED UNIVERSITY CREDENTIAL
# =====================================================
@admin.register(ApprovedUniversityCredential)
class ApprovedUniversityCredentialAdmin(admin.ModelAdmin):
    list_display = ("college_id", "email", "approved_at")
    search_fields = ("college_id", "email")
    list_filter = ("approved_at",)
    ordering = ("-approved_at",)


# =====================================================
# STUDENT LOGIN VALID  ✅ FIXED APP IMPORT
# =====================================================
@admin.register(student_login_valid)
class StudentLoginValidAdmin(admin.ModelAdmin):
    list_display = (
        "StudentID",
        "AISHE_Code",
        "College_name",
        "student_password",
        "created_at",
    )

    search_fields = (
        "StudentID",
        "AISHE_Code",
        "College_name",
    )

    list_filter = (
        "AISHE_Code",
        "College_name",
        "created_at",
    )

    ordering = ("-created_at",)
    readonly_fields = ("created_at",)
    list_per_page = 25

    fieldsets = (
        (
            "Student Information",
            {
                "fields": (
                    "StudentID",
                    "AISHE_Code",
                    "College_name",
                )
            },
        ),
        (
            "Authentication",
            {
                "fields": (
                    "student_password",
                )
            },
        ),
        (
            "System",
            {
                "fields": (
                    "created_at",
                )
            },
        ),
    )
