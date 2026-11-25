from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils import timezone


class Appointment(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'En attente'
        CONFIRMED = 'CONFIRMED', 'Confirmé'
        CANCELLED = 'CANCELLED', 'Annulé'

    # Rôle « praticien »
    doctor = models.ForeignKey(
        'AccountApp.Doctor',
        on_delete=models.CASCADE,
        related_name='appointments',
        verbose_name="médecin",
    )
    # Rôle « demandeur »
    patient = models.ForeignKey(
        'AccountApp.Patient',
        on_delete=models.CASCADE,
        related_name='appointments',
        verbose_name="patient",
    )
    reason = models.TextField("motif")
    prescription = models.FileField(
        "ordonnance",
        upload_to='prescriptions/',
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])],
    )
    status = models.CharField(
        "statut",
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
    )
    duration_minutes = models.PositiveIntegerField("durée (minutes)", default=30)
    appointment_date = models.DateTimeField("date du rendez-vous")
    created_at = models.DateTimeField("créé le", auto_now_add=True)
    updated_at = models.DateTimeField("modifié le", auto_now=True)

    class Meta:
        verbose_name = "rendez-vous"
        verbose_name_plural = "rendez-vous"
        ordering = ['appointment_date']
        constraints = [
            models.UniqueConstraint(
                fields=['doctor', 'appointment_date'],
                name='unique_doctor_appointment_date',
                violation_error_message="Ce médecin a déjà un rendez-vous à cette date et heure.",
            ),
        ]

    def clean(self):
        super().clean()
        if self.appointment_date is None:
            return
        # La règle ne s'applique qu'à la création ou si la date a été modifiée :
        # un rendez-vous passé reste modifiable (ajout de l'ordonnance, changement de statut).
        date_changed = True
        if not self._state.adding:
            old_date = (
                Appointment.objects.filter(pk=self.pk)
                .values_list('appointment_date', flat=True)
                .first()
            )
            date_changed = old_date != self.appointment_date
        if date_changed and self.appointment_date <= timezone.now():
            raise ValidationError(
                {'appointment_date': "La date du rendez-vous doit être postérieure à maintenant."}
            )

    @property
    def is_upcoming(self):
        return self.appointment_date > timezone.now()

    @property
    def can_be_cancelled(self):
        return self.status != self.Status.CANCELLED and self.is_upcoming

    def __str__(self):
        local_date = timezone.localtime(self.appointment_date)
        return f"{self.patient} - {self.doctor} ({local_date:%d/%m/%Y %H:%M})"
