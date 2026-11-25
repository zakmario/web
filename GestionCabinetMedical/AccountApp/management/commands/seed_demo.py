from datetime import date, datetime, time, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from AccountApp.models import Doctor, Patient, Specialty
from AppointmentApp.models import Appointment

DEMO_PASSWORD = 'Demo@2026'

SPECIALTIES = ['Cardiologie', 'Dermatologie', 'Pédiatrie', 'Médecine générale', 'Ophtalmologie']

DOCTORS = [
    {'username': 'dr.benali', 'first_name': 'Amine', 'last_name': 'Ben Ali', 'license_number': '100231',
     'phone': '71234567', 'email': 'amine.benali@cabinet.tn', 'specialties': ['Cardiologie']},
    {'username': 'dr.trabelsi', 'first_name': 'Sarra', 'last_name': 'Trabelsi', 'license_number': '100452',
     'phone': '71345678', 'email': 'sarra.trabelsi@cabinet.tn', 'specialties': ['Dermatologie']},
    {'username': 'dr.gharbi', 'first_name': 'Youssef', 'last_name': 'Gharbi', 'license_number': '100673',
     'phone': '71456789', 'email': 'youssef.gharbi@cabinet.tn', 'specialties': ['Pédiatrie', 'Médecine générale']},
    {'username': 'dr.mansour', 'first_name': 'Leila', 'last_name': 'Mansour', 'license_number': '100894',
     'phone': '71567890', 'email': 'leila.mansour@cabinet.tn', 'specialties': ['Ophtalmologie']},
]

PATIENTS = [
    {'username': 'patient.salah', 'first_name': 'Mohamed', 'last_name': 'Salah', 'national_id': '09876543',
     'phone': '98123456', 'email': 'mohamed.salah@mail.tn', 'birth_date': date(1990, 5, 14)},
    {'username': 'patient.hamdi', 'first_name': 'Ines', 'last_name': 'Hamdi', 'national_id': '07654321',
     'phone': '22345678', 'email': 'ines.hamdi@mail.tn', 'birth_date': date(1985, 11, 2)},
]


class Command(BaseCommand):
    help = "Charge des données de démonstration (spécialités, médecins, patients, rendez-vous)."

    @transaction.atomic
    def handle(self, *args, **options):
        specialties = {
            name: Specialty.objects.get_or_create(name=name)[0] for name in SPECIALTIES
        }

        doctors = []
        for data in DOCTORS:
            data = dict(data)
            names = data.pop('specialties')
            doctor = Doctor.objects.filter(username=data['username']).first()
            if doctor is None:
                doctor = Doctor.objects.create_user(password=DEMO_PASSWORD, **data)
            doctor.specialties.set(specialties[name] for name in names)
            doctors.append(doctor)

        patients = []
        for data in PATIENTS:
            patient = Patient.objects.filter(username=data['username']).first()
            if patient is None:
                patient = Patient.objects.create_user(password=DEMO_PASSWORD, **data)
            patients.append(patient)

        if not Appointment.objects.filter(patient__in=patients).exists():
            tomorrow = timezone.localdate() + timedelta(days=1)
            slots = [
                (doctors[0], patients[0], 0, time(9, 0), "Douleurs thoraciques à l'effort", Appointment.Status.CONFIRMED),
                (doctors[1], patients[0], 2, time(10, 30), "Contrôle d'un grain de beauté", Appointment.Status.PENDING),
                (doctors[2], patients[1], 1, time(14, 0), "Visite de contrôle annuelle", Appointment.Status.PENDING),
                (doctors[3], patients[1], 5, time(11, 0), "Baisse de la vision de loin", Appointment.Status.CANCELLED),
            ]
            for doctor, patient, offset, hour, reason, status in slots:
                appointment_date = timezone.make_aware(
                    datetime.combine(tomorrow + timedelta(days=offset), hour)
                )
                appointment = Appointment(
                    doctor=doctor,
                    patient=patient,
                    appointment_date=appointment_date,
                    reason=reason,
                    status=status,
                )
                appointment.full_clean()
                appointment.save()

        self.stdout.write(self.style.SUCCESS(
            f"Données de démonstration chargées : {len(specialties)} spécialités, "
            f"{len(doctors)} médecins, {len(patients)} patients. "
            f"Mot de passe des comptes de démonstration : {DEMO_PASSWORD}"
        ))
