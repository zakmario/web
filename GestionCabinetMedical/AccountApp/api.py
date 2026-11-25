from rest_framework import permissions, viewsets

from .models import Doctor, Patient, Specialty
from .serializers import DoctorSerializer, PatientSerializer, SpecialtySerializer


class IsAdminOrReadOnly(permissions.BasePermission):
    """Lecture publique, écriture réservée au personnel (is_staff)."""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_staff)


class SpecialtyViewSet(viewsets.ModelViewSet):
    queryset = Specialty.objects.all()
    serializer_class = SpecialtySerializer
    permission_classes = [IsAdminOrReadOnly]


class DoctorViewSet(viewsets.ModelViewSet):
    serializer_class = DoctorSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        queryset = (
            Doctor.objects.prefetch_related('specialties')
            .order_by('last_name', 'first_name')
        )
        if not self.request.user.is_staff:
            queryset = queryset.filter(is_active=True)
        specialty = self.request.query_params.get('specialty', '')
        if specialty.isdigit():
            queryset = queryset.filter(specialties__id=specialty)
        return queryset


class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.order_by('last_name', 'first_name')
    serializer_class = PatientSerializer
    permission_classes = [permissions.IsAdminUser]
