from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.hashers import make_password, check_password


class StudentRegistration(models.Model):
    """
    Registration data - main student info
    """
    college_name = models.CharField(max_length=150)
    college_email = models.EmailField(unique=True)
    college_id = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=128)  # we'll store hashed password
    
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Student Registration"
        verbose_name_plural = "Student Registrations"

    def __str__(self):
        return f"{self.college_id} - {self.college_name}"

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)


class StudentLogin(models.Model):
    """
    Login credentials - separate table as requested
    """
    registration = models.OneToOneField(
        StudentRegistration,
        on_delete=models.CASCADE,
        related_name='login_credentials'
    )
    
    college_id = models.CharField(max_length=50, unique=True)
    college_name = models.CharField(max_length=150)
    password = models.CharField(max_length=128)  # hashed password

    last_login = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Login creds for {self.college_id}"

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)
    
from django.db import models

class student_login_valid(models.Model):
    AISHE_Code = models.CharField(max_length=50)
    College_name = models.CharField(max_length=255)
    StudentID = models.CharField(max_length=100, unique=True)
    student_password = models.CharField(max_length=100)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.StudentID
