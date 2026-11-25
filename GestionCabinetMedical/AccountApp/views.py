from django.contrib import messages
from django.contrib.auth import login
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import PatientRegistrationForm
from .models import Doctor, Specialty


def home(request):
    doctors = (
        Doctor.objects.filter(is_active=True)
        .prefetch_related('specialties')
        .order_by('last_name', 'first_name')
    )
    query = request.GET.get('q', '').strip()
    specialty_id = request.GET.get('specialty', '')

    if specialty_id.isdigit():
        doctors = doctors.filter(specialties__id=specialty_id)
    else:
        specialty_id = ''
    if query:
        doctors = doctors.filter(
            Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(specialties__name__icontains=query)
        ).distinct()

    return render(request, 'AccountApp/home.html', {
        'doctors': doctors,
        'specialties': Specialty.objects.all(),
        'selected_specialty': specialty_id,
        'query': query,
    })


def doctor_detail(request, pk):
    doctor = get_object_or_404(
        Doctor.objects.prefetch_related('specialties'), pk=pk, is_active=True
    )
    return render(request, 'AccountApp/doctor_detail.html', {'doctor': doctor})


def register(request):
    if request.user.is_authenticated:
        return redirect('home')
    form = PatientRegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        patient = form.save()
        login(request, patient)
        messages.success(request, f"Bienvenue {patient.first_name}, votre compte patient a été créé.")
        return redirect('home')
    return render(request, 'AccountApp/register.html', {'form': form})
