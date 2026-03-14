from django.db import models
from django.contrib.auth.models import AbstractUser


class Organization(models.Model):
    name = models.CharField(max_length=255)

    primary_color = models.CharField(max_length=7, default="#000000")
    secondary_color = models.CharField(max_length=7, default="#ffffff")
    tertiary_color = models.CharField(max_length=7, default="#cccccc")

    logo = models.ImageField(upload_to="org_logos/", null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class User(AbstractUser):

    ROLE_CHOICES = (
        ("SUPERADMIN", "Super Admin"),
        ("ORG-ADMIN", "Organization Admin"),
        ("STUDENT", "Student"),
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="users"
    )

    face_encoding = models.JSONField(null=True, blank=True)

    enrollment_no = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.username} ({self.role})"
    

# To track Entry/Exit logs
class EventLog(models.Model):

    EVENT_CHOICES = (
        ("ENTRY", "Entry"),
        ("EXIT", "Exit"),
    )

    event = models.CharField(max_length=20, choices=EVENT_CHOICES)

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.event} - {self.user}"