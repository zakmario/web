from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from AccountApp.utils import get_patient, get_role

from .models import Appointment
from .serializers import (
    AppointmentSerializer,
    DoctorAppointmentSerializer,
    PatientAppointmentSerializer,
)


class AppointmentPermission(permissions.BasePermission):
    """Actions autorisées selon le rôle de l'utilisateur connecté."""

    allowed_actions = {
        'patient': {'list', 'retrieve', 'create', 'cancel', 'metadata'},
        'doctor': {'list', 'retrieve', 'update', 'partial_update', 'cancel', 'confirm', 'metadata'},
    }

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.is_staff:
            return True
        role = get_role(request.user)
        return view.action in self.allowed_actions.get(role, set())


class AppointmentViewSet(viewsets.ModelViewSet):
    permission_classes = [AppointmentPermission]

    def get_queryset(self):
        queryset = Appointment.objects.select_related('doctor', 'patient')
        user = self.request.user
        role = get_role(user)
        if role == 'patient':
            queryset = queryset.filter(patient_id=user.pk)
        elif role == 'doctor':
            queryset = queryset.filter(doctor_id=user.pk)
        elif not user.is_staff:
            queryset = queryset.none()

        status_filter = self.request.query_params.get('status')
        if status_filter in Appointment.Status.values:
            queryset = queryset.filter(status=status_filter)
        return queryset

    def get_serializer_class(self):
        if self.request.user.is_staff:
            return AppointmentSerializer
        role = get_role(self.request.user)
        if role == 'patient':
            return PatientAppointmentSerializer
        if role == 'doctor':
            return DoctorAppointmentSerializer
        return AppointmentSerializer

    def perform_create(self, serializer):
        patient = get_patient(self.request.user)
        if patient is not None:
            serializer.save(patient=patient)
        else:
            serializer.save()

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        appointment = self.get_object()
        if not appointment.can_be_cancelled:
            return Response(
                {'detail': "Ce rendez-vous ne peut plus être annulé."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        appointment.status = Appointment.Status.CANCELLED
        appointment.save(update_fields=['status', 'updated_at'])
        return Response(self.get_serializer(appointment).data)

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        appointment = self.get_object()
        if appointment.status != Appointment.Status.PENDING:
            return Response(
                {'detail': "Seul un rendez-vous en attente peut être confirmé."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        appointment.status = Appointment.Status.CONFIRMED
        appointment.save(update_fields=['status', 'updated_at'])
        return Response(self.get_serializer(appointment).data)
