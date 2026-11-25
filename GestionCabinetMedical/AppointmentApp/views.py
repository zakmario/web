from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from AccountApp.utils import get_doctor, get_patient

from .forms import AppointmentForm, PrescriptionForm
from .models import Appointment


@login_required
def appointment_list(request):
    appointments = Appointment.objects.select_related('doctor', 'patient')
    patient = get_patient(request.user)
    doctor = get_doctor(request.user)

    if patient:
        appointments = appointments.filter(patient=patient)
    elif doctor:
        appointments = appointments.filter(doctor=doctor)
    elif not request.user.is_staff:
        appointments = appointments.none()

    status = request.GET.get('status', '')
    if status in Appointment.Status.values:
        appointments = appointments.filter(status=status)
    else:
        status = ''

    return render(request, 'AppointmentApp/appointment_list.html', {
        'appointments': appointments,
        'is_patient': patient is not None,
        'is_doctor': doctor is not None,
        'statuses': Appointment.Status.choices,
        'selected_status': status,
    })


@login_required
def appointment_create(request):
    patient = get_patient(request.user)
    if patient is None:
        messages.error(request, "Seuls les patients peuvent prendre un rendez-vous.")
        return redirect('home')

    initial = {}
    doctor_id = request.GET.get('doctor', '')
    if doctor_id.isdigit():
        initial['doctor'] = doctor_id

    form = AppointmentForm(
        request.POST or None,
        initial=initial,
        instance=Appointment(patient=patient),
    )
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Votre demande de rendez-vous a été enregistrée.")
        return redirect('appointment_list')
    return render(request, 'AppointmentApp/appointment_form.html', {'form': form})


@login_required
@require_POST
def appointment_cancel(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    if request.user.pk not in (appointment.patient_id, appointment.doctor_id):
        raise PermissionDenied
    if appointment.can_be_cancelled:
        appointment.status = Appointment.Status.CANCELLED
        appointment.save(update_fields=['status', 'updated_at'])
        messages.success(request, "Le rendez-vous a été annulé.")
    else:
        messages.error(request, "Ce rendez-vous ne peut plus être annulé.")
    return redirect('appointment_list')


@login_required
@require_POST
def appointment_confirm(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk, doctor_id=request.user.pk)
    if appointment.status == Appointment.Status.PENDING:
        appointment.status = Appointment.Status.CONFIRMED
        appointment.save(update_fields=['status', 'updated_at'])
        messages.success(request, "Le rendez-vous a été confirmé.")
    else:
        messages.error(request, "Seul un rendez-vous en attente peut être confirmé.")
    return redirect('appointment_list')


@login_required
def appointment_prescription(request, pk):
    appointment = get_object_or_404(
        Appointment.objects.select_related('doctor', 'patient'),
        pk=pk,
        doctor_id=request.user.pk,
    )
    form = PrescriptionForm(request.POST or None, request.FILES or None, instance=appointment)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "L'ordonnance a été enregistrée.")
        return redirect('appointment_list')
    return render(request, 'AppointmentApp/prescription_form.html', {
        'form': form,
        'appointment': appointment,
    })
