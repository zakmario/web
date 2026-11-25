from django.contrib import admin

from .models import Appointment


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('appointment_date', 'doctor', 'patient', 'status', 'duration_minutes')
    list_filter = ('status', 'doctor')
    search_fields = (
        'reason',
        'doctor__first_name', 'doctor__last_name',
        'patient__first_name', 'patient__last_name', 'patient__national_id',
    )
    date_hierarchy = 'appointment_date'
    autocomplete_fields = ('doctor', 'patient')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {'fields': ('doctor', 'patient', 'appointment_date', 'duration_minutes', 'status')}),
        ("Consultation", {'fields': ('reason', 'prescription')}),
        ("Suivi", {'fields': ('created_at', 'updated_at')}),
    )
