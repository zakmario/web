from datetime import timedelta

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from AccountApp.tests import create_doctor, create_patient

from .models import Appointment


def future(days=1):
    return (timezone.now() + timedelta(days=days)).replace(second=0, microsecond=0)


class AppointmentModelTests(TestCase):
    def setUp(self):
        self.doctor = create_doctor()
        self.patient = create_patient()

    def build(self, **kwargs):
        data = {'doctor': self.doctor, 'patient': self.patient, 'reason': 'Contrôle',
                'appointment_date': future()}
        data.update(kwargs)
        return Appointment(**data)

    def test_defaults(self):
        appointment = self.build()
        appointment.full_clean()
        appointment.save()
        self.assertEqual(appointment.status, Appointment.Status.PENDING)
        self.assertEqual(appointment.duration_minutes, 30)

    def test_date_in_the_past_is_rejected(self):
        with self.assertRaises(ValidationError) as ctx:
            self.build(appointment_date=timezone.now() - timedelta(hours=1)).full_clean()
        self.assertIn('appointment_date', ctx.exception.message_dict)

    def test_past_appointment_stays_editable(self):
        appointment = self.build()
        appointment.save()
        Appointment.objects.filter(pk=appointment.pk).update(
            appointment_date=timezone.now() - timedelta(days=1)
        )
        appointment.refresh_from_db()
        appointment.status = Appointment.Status.CONFIRMED
        appointment.full_clean()  # ne doit pas lever d'exception

    def test_moving_appointment_to_the_past_is_rejected(self):
        appointment = self.build()
        appointment.save()
        appointment.appointment_date = timezone.now() - timedelta(days=1)
        with self.assertRaises(ValidationError):
            appointment.full_clean()

    def test_doctor_cannot_have_two_appointments_at_same_date(self):
        date = future()
        self.build(appointment_date=date).save()
        with self.assertRaises(ValidationError) as ctx:
            self.build(appointment_date=date).full_clean()
        self.assertIn("déjà un rendez-vous", str(ctx.exception))

    def test_prescription_must_be_pdf(self):
        appointment = self.build(prescription=SimpleUploadedFile('ordonnance.txt', b'x'))
        with self.assertRaises(ValidationError) as ctx:
            appointment.full_clean()
        self.assertIn('prescription', ctx.exception.message_dict)


@override_settings(MEDIA_ROOT='test_media')
class AppointmentViewTests(TestCase):
    def setUp(self):
        self.doctor = create_doctor()
        self.patient = create_patient()

    def tearDown(self):
        import shutil
        shutil.rmtree('test_media', ignore_errors=True)

    def test_booking_requires_login(self):
        response = self.client.get(reverse('appointment_create'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('appointment_create')}")

    def test_patient_books_appointment(self):
        self.client.force_login(self.patient)
        response = self.client.post(reverse('appointment_create'), {
            'doctor': self.doctor.pk,
            'appointment_date': timezone.localtime(future()).strftime('%Y-%m-%dT%H:%M'),
            'reason': 'Consultation',
        })
        self.assertRedirects(response, reverse('appointment_list'))
        appointment = Appointment.objects.get()
        self.assertEqual(appointment.patient, self.patient)
        self.assertEqual(appointment.status, Appointment.Status.PENDING)

    def test_doctor_cannot_book(self):
        self.client.force_login(self.doctor)
        response = self.client.get(reverse('appointment_create'))
        self.assertRedirects(response, reverse('home'))

    def test_lists_are_filtered_by_role(self):
        other_patient = create_patient(username='other', national_id='99887766')
        Appointment.objects.create(doctor=self.doctor, patient=self.patient, reason='a', appointment_date=future(1))
        Appointment.objects.create(doctor=self.doctor, patient=other_patient, reason='b', appointment_date=future(2))
        self.client.force_login(self.patient)
        self.assertEqual(len(self.client.get(reverse('appointment_list')).context['appointments']), 1)
        self.client.force_login(self.doctor)
        self.assertEqual(len(self.client.get(reverse('appointment_list')).context['appointments']), 2)

    def test_doctor_confirms_and_patient_cancels(self):
        appointment = Appointment.objects.create(
            doctor=self.doctor, patient=self.patient, reason='a', appointment_date=future()
        )
        self.client.force_login(self.doctor)
        self.client.post(reverse('appointment_confirm', args=[appointment.pk]))
        appointment.refresh_from_db()
        self.assertEqual(appointment.status, Appointment.Status.CONFIRMED)

        self.client.force_login(self.patient)
        self.client.post(reverse('appointment_cancel', args=[appointment.pk]))
        appointment.refresh_from_db()
        self.assertEqual(appointment.status, Appointment.Status.CANCELLED)

    def test_other_patient_cannot_cancel(self):
        appointment = Appointment.objects.create(
            doctor=self.doctor, patient=self.patient, reason='a', appointment_date=future()
        )
        intruder = create_patient(username='intrus', national_id='99887766')
        self.client.force_login(intruder)
        response = self.client.post(reverse('appointment_cancel', args=[appointment.pk]))
        self.assertEqual(response.status_code, 403)

    def test_doctor_uploads_prescription_on_past_appointment(self):
        appointment = Appointment.objects.create(
            doctor=self.doctor, patient=self.patient, reason='a',
            appointment_date=timezone.now() - timedelta(days=1),
        )
        self.client.force_login(self.doctor)
        response = self.client.post(
            reverse('appointment_prescription', args=[appointment.pk]),
            {'prescription': SimpleUploadedFile('ordonnance.pdf', b'%PDF-1.4', 'application/pdf')},
        )
        self.assertRedirects(response, reverse('appointment_list'))
        appointment.refresh_from_db()
        self.assertTrue(appointment.prescription.name.startswith('prescriptions/'))


class AppointmentApiTests(APITestCase):
    def setUp(self):
        self.doctor = create_doctor()
        self.patient = create_patient()

    def test_anonymous_is_rejected(self):
        self.assertEqual(self.client.get('/api/appointments/').status_code, 403)

    def test_patient_creates_appointment_for_himself(self):
        self.client.force_authenticate(self.patient)
        response = self.client.post('/api/appointments/', {
            'doctor': self.doctor.pk, 'appointment_date': future().isoformat(), 'reason': 'Fièvre',
            'status': 'CONFIRMED',  # ignoré : champ en lecture seule pour un patient
        })
        self.assertEqual(response.status_code, 201, response.data)
        appointment = Appointment.objects.get()
        self.assertEqual(appointment.patient, self.patient)
        self.assertEqual(appointment.status, Appointment.Status.PENDING)

    def test_api_rejects_past_date_and_duplicates(self):
        self.client.force_authenticate(self.patient)
        past = self.client.post('/api/appointments/', {
            'doctor': self.doctor.pk, 'appointment_date': (timezone.now() - timedelta(days=1)).isoformat(),
            'reason': 'x',
        })
        self.assertEqual(past.status_code, 400)
        self.assertIn('appointment_date', past.data)

        date = future().isoformat()
        self.client.post('/api/appointments/', {'doctor': self.doctor.pk, 'appointment_date': date, 'reason': 'x'})
        duplicate = self.client.post('/api/appointments/', {'doctor': self.doctor.pk, 'appointment_date': date, 'reason': 'y'})
        self.assertEqual(duplicate.status_code, 400)

    def test_doctor_cannot_create_but_can_confirm(self):
        appointment = Appointment.objects.create(
            doctor=self.doctor, patient=self.patient, reason='a', appointment_date=future()
        )
        self.client.force_authenticate(self.doctor)
        response = self.client.post('/api/appointments/', {
            'doctor': self.doctor.pk, 'patient': self.patient.pk,
            'appointment_date': future(3).isoformat(), 'reason': 'x',
        })
        self.assertEqual(response.status_code, 403)
        response = self.client.post(f'/api/appointments/{appointment.pk}/confirm/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'CONFIRMED')

    def test_patient_only_sees_own_appointments(self):
        other = create_patient(username='other', national_id='99887766')
        Appointment.objects.create(doctor=self.doctor, patient=self.patient, reason='a', appointment_date=future(1))
        Appointment.objects.create(doctor=self.doctor, patient=other, reason='b', appointment_date=future(2))
        self.client.force_authenticate(self.patient)
        response = self.client.get('/api/appointments/')
        self.assertEqual(response.data['count'], 1)
