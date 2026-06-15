#university_app/models

from django.db import models
from django.utils import timezone


class UniversityRequest(models.Model):
    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Approved", "Approved"),
        ("Rejected", "Rejected"),
    ]

    college_id = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="College ID"
    )
    name = models.CharField(max_length=255)
    address = models.TextField()
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=20)
    country = models.CharField(max_length=100)

    # ❌ NOT UNIQUE
    university_email = models.EmailField()

    contact_number = models.CharField(max_length=20)
    website = models.URLField(max_length=500, blank=True, null=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="Pending"
    )
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.college_id} – {self.name}"
