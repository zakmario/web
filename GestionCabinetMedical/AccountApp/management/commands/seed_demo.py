from datetime import date, datetime, time, timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
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
    {'username': 'dr.chaabane', 'first_name': 'Karim', 'last_name': 'Chaabane', 'license_number': '101015',
     'phone': '71678901', 'email': 'karim.chaabane@cabinet.tn', 'specialties': ['Médecine générale', 'Cardiologie']},
]

PATIENTS = [
    {'username': 'patient.salah', 'first_name': 'Mohamed', 'last_name': 'Salah', 'national_id': '09876543',
     'phone': '98123456', 'email': 'mohamed.salah@mail.tn', 'birth_date': date(1990, 5, 14)},
    {'username': 'patient.hamdi', 'first_name': 'Ines', 'last_name': 'Hamdi', 'national_id': '07654321',
     'phone': '22345678', 'email': 'ines.hamdi@mail.tn', 'birth_date': date(1985, 11, 2)},
    {'username': 'patient.jlassi', 'first_name': 'Rania', 'last_name': 'Jlassi', 'national_id': '05432198',
     'phone': '55123987', 'email': 'rania.jlassi@mail.tn', 'birth_date': date(2015, 3, 22)},
    {'username': 'patient.bouazizi', 'first_name': 'Hichem', 'last_name': 'Bouazizi', 'national_id': '03219876',
     'phone': '29876543', 'email': 'hichem.bouazizi@mail.tn', 'birth_date': date(1962, 8, 9)},
    {'username': 'patient.khelifi', 'first_name': 'Nour', 'last_name': 'Khelifi', 'national_id': '11223344',
     'phone': '50987123', 'email': 'nour.khelifi@mail.tn', 'birth_date': date(1998, 1, 30)},
]

# Groupe « Secrétaires » : view/add/change sur Appointment, view seul sur le reste (pas de delete).
SECRETARY_GROUP = 'Secrétaires'
SECRETARY_PERMISSIONS = [
    'view_appointment', 'add_appointment', 'change_appointment',
    'view_doctor', 'view_patient', 'view_specialty',
]
SECRETARY_USERNAME = 'secretaire1'


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

        tomorrow = timezone.localdate() + timedelta(days=1)
        slots = [
            (0, 0, 0, time(9, 0), "Douleurs thoraciques à l'effort", Appointment.Status.CONFIRMED),
            (1, 0, 2, time(10, 30), "Contrôle d'un grain de beauté", Appointment.Status.PENDING),
            (2, 1, 1, time(14, 0), "Visite de contrôle annuelle", Appointment.Status.PENDING),
            (3, 1, 5, time(11, 0), "Baisse de la vision de loin", Appointment.Status.CANCELLED),
            (2, 2, 0, time(15, 30), "Vaccination de rappel", Appointment.Status.CONFIRMED),
            (4, 3, 1, time(8, 30), "Suivi de l'hypertension", Appointment.Status.CONFIRMED),
            (0, 3, 3, time(9, 30), "Électrocardiogramme de contrôle", Appointment.Status.PENDING),
            (4, 4, 2, time(16, 0), "Fièvre et maux de gorge", Appointment.Status.PENDING),
            (1, 4, 4, time(11, 30), "Eczéma sur les mains", Appointment.Status.PENDING),
            (3, 2, 6, time(10, 0), "Examen de la vue (rentrée scolaire)", Appointment.Status.CONFIRMED),
        ]
        created = 0
        for doctor_idx, patient_idx, offset, hour, reason, status in slots:
            doctor, patient = doctors[doctor_idx], patients[patient_idx]
            if Appointment.objects.filter(doctor=doctor, patient=patient, reason=reason).exists():
                continue
            appointment = Appointment(
                doctor=doctor,
                patient=patient,
                appointment_date=timezone.make_aware(
                    datetime.combine(tomorrow + timedelta(days=offset), hour)
                ),
                reason=reason,
                status=status,
            )
            appointment.full_clean()
            appointment.save()
            created += 1

        group, _ = Group.objects.get_or_create(name=SECRETARY_GROUP)
        group.permissions.set(Permission.objects.filter(
            codename__in=SECRETARY_PERMISSIONS,
            content_type__app_label__in=['AccountApp', 'AppointmentApp'],
        ))
        secretary = get_user_model().objects.filter(username=SECRETARY_USERNAME).first()
        if secretary is None:
            secretary = get_user_model().objects.create_user(
                username=SECRETARY_USERNAME, password=DEMO_PASSWORD, email='secretaire1@cabinet.tn',
                is_staff=True,
            )
        secretary.groups.add(group)

        self.stdout.write(self.style.SUCCESS(
            f"Données de démonstration chargées : {len(specialties)} spécialités, "
            f"{len(doctors)} médecins, {len(patients)} patients, {created} nouveau(x) rendez-vous ; "
            f"groupe « {SECRETARY_GROUP} » et compte staff « {SECRETARY_USERNAME} ». "
            f"Mot de passe des comptes de démonstration : {DEMO_PASSWORD}"
        ))
