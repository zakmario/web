from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator, RegexValidator
from django.db import models
from django.utils import timezone

phone_validator = RegexValidator(
    regex=r'^\d{8}$',
    message="Le numéro de téléphone doit contenir exactement 8 chiffres.",
)
national_id_validator = RegexValidator(
    regex=r'^\d{8}$',
    message="Le numéro de CIN doit contenir exactement 8 chiffres.",
)


def validate_past_date(value):
    if value >= timezone.localdate():
        raise ValidationError("La date de naissance doit être antérieure à la date du jour.")


class User(AbstractUser):
    pass


class Specialty(models.Model):
    name = models.CharField("nom", max_length=100, unique=True)

    class Meta:
        verbose_name = "spécialité"
        verbose_name_plural = "spécialités"
        ordering = ['name']

    def __str__(self):
        return self.name


class Doctor(User):
    license_number = models.CharField(
        "numéro d'inscription à l'ordre",
        max_length=6,
        unique=True,
        validators=[MinLengthValidator(6)],
    )
    phone = models.CharField("téléphone", max_length=8, validators=[phone_validator])
    specialties = models.ManyToManyField(
        Specialty,
        related_name='doctors',
        verbose_name="spécialités",
    )

    class Meta:
        verbose_name = "médecin"
        verbose_name_plural = "médecins"

    def __str__(self):
        return f"Dr {self.first_name} {self.last_name}"


class Patient(User):
    national_id = models.CharField(
        "numéro de CIN",
        max_length=8,
        unique=True,
        validators=[national_id_validator],
    )
    phone = models.CharField("téléphone", max_length=8, validators=[phone_validator])
    birth_date = models.DateField("date de naissance", validators=[validate_past_date])

    class Meta:
        verbose_name = "patient"
        verbose_name_plural = "patients"

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
