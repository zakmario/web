from django import forms

from AccountApp.forms import BootstrapFormMixin
from AccountApp.models import Doctor

from .models import Appointment


class DoctorChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, doctor):
        specialties = ", ".join(s.name for s in doctor.specialties.all())
        return f"{doctor} ({specialties})" if specialties else str(doctor)


class AppointmentForm(BootstrapFormMixin, forms.ModelForm):
    doctor = DoctorChoiceField(
        queryset=Doctor.objects.filter(is_active=True)
        .prefetch_related('specialties')
        .order_by('last_name', 'first_name'),
        label="Médecin",
    )

    class Meta:
        model = Appointment
        fields = ('doctor', 'appointment_date', 'reason')
        widgets = {
            'appointment_date': forms.DateTimeInput(
                attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'
            ),
            'reason': forms.Textarea(attrs={'rows': 4}),
        }


class PrescriptionForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ('prescription',)
        widgets = {
            'prescription': forms.ClearableFileInput(attrs={'accept': '.pdf'}),
        }
