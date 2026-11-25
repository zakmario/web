from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase

from .models import Doctor, Patient, Specialty


def create_doctor(**kwargs):
    data = {'username': 'dr.test', 'password': 'Secret@123', 'first_name': 'Ali',
            'last_name': 'Ben', 'license_number': '123456', 'phone': '12345678'}
    data.update(kwargs)
    return Doctor.objects.create_user(**data)


def create_patient(**kwargs):
    data = {'username': 'patient.test', 'password': 'Secret@123', 'first_name': 'Sami',
            'last_name': 'Kefi', 'national_id': '11223344', 'phone': '87654321',
            'birth_date': date(1990, 1, 1)}
    data.update(kwargs)
    return Patient.objects.create_user(**data)


class ModelTests(TestCase):
    def test_patient_pk_is_user_pk(self):
        patient = create_patient()
        self.assertEqual(patient.pk, get_user_model().objects.get(username='patient.test').pk)
        self.assertTrue(patient.check_password('Secret@123'))

    def test_license_number_must_have_6_characters(self):
        doctor = Doctor(username='x', password='x', license_number='123', phone='12345678')
        with self.assertRaises(ValidationError) as ctx:
            doctor.full_clean(exclude=['specialties'])
        self.assertIn('license_number', ctx.exception.message_dict)

    def test_phone_must_have_8_digits(self):
        doctor = Doctor(username='x', password='x', license_number='123456', phone='12ab5678')
        with self.assertRaises(ValidationError) as ctx:
            doctor.full_clean()
        self.assertIn('phone', ctx.exception.message_dict)

    def test_national_id_must_have_8_digits(self):
        patient = Patient(username='y', password='x', national_id='1234567a',
                          phone='12345678', birth_date=date(1990, 1, 1))
        with self.assertRaises(ValidationError) as ctx:
            patient.full_clean()
        self.assertIn('national_id', ctx.exception.message_dict)

    def test_birth_date_must_be_in_the_past(self):
        patient = Patient(username='y', password='x', national_id='12345678',
                          phone='12345678', birth_date=date.today())
        with self.assertRaises(ValidationError) as ctx:
            patient.full_clean()
        self.assertIn('birth_date', ctx.exception.message_dict)

    def test_national_id_is_unique(self):
        create_patient()
        duplicate = Patient(username='other', password='x', national_id='11223344',
                            phone='12345678', birth_date=date(1990, 1, 1))
        with self.assertRaises(ValidationError) as ctx:
            duplicate.full_clean()
        self.assertIn('national_id', ctx.exception.message_dict)


class FrontOfficeTests(TestCase):
    def setUp(self):
        self.cardio = Specialty.objects.create(name='Cardiologie')
        self.derma = Specialty.objects.create(name='Dermatologie')
        self.doctor = create_doctor()
        self.doctor.specialties.add(self.cardio)
        self.other = create_doctor(username='dr.other', license_number='654321', last_name='Zed')
        self.other.specialties.add(self.derma)

    def test_home_lists_doctors(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dr Ali Ben')
        self.assertContains(response, 'Cardiologie')
        self.assertEqual(len(response.context['doctors']), 2)

    def test_home_filters_by_specialty(self):
        response = self.client.get(reverse('home'), {'specialty': self.derma.pk})
        self.assertEqual(list(response.context['doctors']), [self.other])

    def test_home_search(self):
        response = self.client.get(reverse('home'), {'q': 'cardio'})
        self.assertEqual(list(response.context['doctors']), [self.doctor])

    def test_home_hides_inactive_doctors(self):
        self.other.is_active = False
        self.other.save()
        response = self.client.get(reverse('home'))
        self.assertEqual(list(response.context['doctors']), [self.doctor])

    def test_doctor_detail(self):
        response = self.client.get(reverse('doctor_detail', args=[self.doctor.pk]))
        self.assertContains(response, self.doctor.license_number)

    def test_register_creates_patient_and_logs_in(self):
        response = self.client.post(reverse('register'), {
            'username': 'nouveau', 'first_name': 'Nour', 'last_name': 'Ayari',
            'email': 'nour@mail.tn', 'national_id': '12345678', 'phone': '55123456',
            'birth_date': '1995-03-10', 'password1': 'Motdepasse@2026', 'password2': 'Motdepasse@2026',
        })
        self.assertRedirects(response, reverse('home'))
        patient = Patient.objects.get(username='nouveau')
        self.assertEqual(int(self.client.session['_auth_user_id']), patient.pk)

    def test_register_rejects_username_of_a_doctor(self):
        response = self.client.post(reverse('register'), {
            'username': 'DR.TEST', 'first_name': 'Nour', 'last_name': 'Ayari',
            'email': 'nour@mail.tn', 'national_id': '12345678', 'phone': '55123456',
            'birth_date': '1995-03-10', 'password1': 'Motdepasse@2026', 'password2': 'Motdepasse@2026',
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('username', response.context['form'].errors)


class AccountApiTests(APITestCase):
    def setUp(self):
        self.specialty = Specialty.objects.create(name='Pédiatrie')
        self.admin = get_user_model().objects.create_superuser('admin', 'a@a.tn', 'Secret@123')

    def test_doctors_are_public(self):
        create_doctor().specialties.add(self.specialty)
        response = self.client.get('/api/doctors/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'][0]['specialty_names'], ['Pédiatrie'])

    def test_only_staff_can_create_doctor(self):
        payload = {
            'username': 'dr.api', 'password': 'Secret@123', 'first_name': 'A', 'last_name': 'B',
            'license_number': '777777', 'phone': '12345678', 'specialties': [self.specialty.pk],
        }
        self.assertEqual(self.client.post('/api/doctors/', payload).status_code, 403)
        self.client.force_authenticate(self.admin)
        response = self.client.post('/api/doctors/', payload)
        self.assertEqual(response.status_code, 201)
        doctor = Doctor.objects.get(username='dr.api')
        self.assertTrue(doctor.check_password('Secret@123'))
        self.assertEqual(list(doctor.specialties.all()), [self.specialty])

    def test_license_number_is_read_only_after_creation(self):
        doctor = create_doctor()
        self.client.force_authenticate(self.admin)
        self.client.patch(f'/api/doctors/{doctor.pk}/', {'license_number': '999999', 'phone': '11111111'})
        doctor.refresh_from_db()
        self.assertEqual(doctor.license_number, '123456')
        self.assertEqual(doctor.phone, '11111111')

    def test_patients_are_reserved_to_staff(self):
        patient = create_patient()
        self.client.force_authenticate(patient)
        self.assertEqual(self.client.get('/api/patients/').status_code, 403)
        self.client.force_authenticate(self.admin)
        self.assertEqual(self.client.get('/api/patients/').status_code, 200)
