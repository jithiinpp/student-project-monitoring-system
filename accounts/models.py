from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):

    ROLE_CHOICES = [
        ("STUDENT", "Student"),
        ("COORDINATOR", "Coordinator"),
        ("EXPERT", "Domain Expert"),
        ("GUIDE", "Guide"),
        ("PANEL", "Panel Member"),
    ]

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default="STUDENT"
    )

    phone = models.CharField(
        max_length=15,
        blank=True,
        null=True
    )

    roll_number = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    department = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    semester = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    batch = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    def __str__(self):
        return self.username