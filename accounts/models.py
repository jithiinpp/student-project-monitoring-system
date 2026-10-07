from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):

    is_student = models.BooleanField(default=False)
    is_coordinator = models.BooleanField(default=False)
    is_faculty = models.BooleanField(default=False)
    is_expert = models.BooleanField(default=False)
    is_guide = models.BooleanField(default=False)
    is_panel = models.BooleanField(default=False)

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

    domain_of_expertise = models.CharField(
        max_length=200,
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