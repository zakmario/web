import copy

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import Appointment


class AppointmentSerializer(serializers.ModelSerializer):
    doctor_name = serializers.StringRelatedField(source='doctor', read_only=True)
    patient_name = serializers.StringRelatedField(source='patient', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Appointment
        fields = (
            'id', 'doctor', 'doctor_name', 'patient', 'patient_name',
            'appointment_date', 'duration_minutes', 'reason',
            'status', 'status_display', 'prescription',
            'created_at', 'updated_at',
        )
        read_only_fields = ('created_at', 'updated_at')

    def validate(self, attrs):
        # DRF n'appelle pas Model.clean() : on l'exécute sur une copie de l'instance
        instance = copy.copy(self.instance) if self.instance else Appointment()
        for attr, value in attrs.items():
            setattr(instance, attr, value)
        try:
            instance.clean()
        except DjangoValidationError as error:
            raise serializers.ValidationError(error.message_dict)
        return attrs


class PatientAppointmentSerializer(AppointmentSerializer):
    """Un patient choisit le médecin, la date et le motif ; le reste est géré par le cabinet."""

    class Meta(AppointmentSerializer.Meta):
        read_only_fields = (
            'patient', 'status', 'prescription', 'duration_minutes',
            'created_at', 'updated_at',
        )


class DoctorAppointmentSerializer(AppointmentSerializer):
    """Un médecin ne modifie que le statut et l'ordonnance de ses rendez-vous."""

    class Meta(AppointmentSerializer.Meta):
        read_only_fields = (
            'doctor', 'patient', 'appointment_date', 'duration_minutes', 'reason',
            'created_at', 'updated_at',
        )
