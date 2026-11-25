from .models import Doctor, Patient

# Héritage multi-tables : doctor.pk == patient.pk == user.pk


def get_patient(user):
    if not user.is_authenticated:
        return None
    return Patient.objects.filter(pk=user.pk).first()


def get_doctor(user):
    if not user.is_authenticated:
        return None
    return Doctor.objects.filter(pk=user.pk).first()


def get_role(user):
    if not user.is_authenticated:
        return None
    if Patient.objects.filter(pk=user.pk).exists():
        return 'patient'
    if Doctor.objects.filter(pk=user.pk).exists():
        return 'doctor'
    if user.is_staff:
        return 'staff'
    return None
