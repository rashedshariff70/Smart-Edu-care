# admin_app/models.py

from django.db import models
from django.contrib.auth.models import User

class ApprovedUniversityAccount(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='university_account')
    college_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    university_email = models.EmailField(unique=True)  # ✅ Make email unique
    country = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    pincode = models.CharField(max_length=20, blank=True)
    contact_number = models.CharField(max_length=20, blank=True)
    website = models.URLField(max_length=500, blank=True, null=True)
    approved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Approved University"
        verbose_name_plural = "Approved Universities"
        ordering = ["-approved_at"]

    def __str__(self):
        return f"{self.name} ({self.college_id})"

from django.db import models

class ApprovedUniversityCredential(models.Model):
    college_id = models.CharField(max_length=100)
    name = models.CharField(max_length=255)
    email = models.EmailField()
    password = models.CharField(max_length=255)
    approved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "approved_university_credentials"
        ordering = ["-approved_at"]

    def __str__(self):
        return f"{self.college_id} ({self.email})"
