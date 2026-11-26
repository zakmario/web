from datetime import timedelta

from django.contrib import admin
from django.utils import timezone

from .models import Appointment


class AppointmentInline(admin.StackedInline):
    """Historique des rendez-vous, affiché dans la fiche du patient (PatientAdmin)."""

    model = Appointment
    fk_name = 'patient'
    extra = 0
    fields = ('doctor', 'appointment_date', 'duration_minutes', 'status', 'reason', 'prescription')
    autocomplete_fields = ('doctor',)
    ordering = ('-appointment_date',)
    show_change_link = True


class DateRangeFilter(admin.SimpleListFilter):
    """Filtre personnalisé selon la date du rendez-vous."""

    title = "période"
    parameter_name = 'periode'

    def lookups(self, request, model_admin):
        return (
            ('today', "Aujourd'hui"),
            ('week', "Cette semaine"),
            ('upcoming', "À venir"),
        )

    def queryset(self, request, queryset):
        today = timezone.localdate()
        if self.value() == 'today':
            return queryset.filter(appointment_date__date=today)
        if self.value() == 'week':
            monday = today - timedelta(days=today.weekday())
            sunday = monday + timedelta(days=6)
            return queryset.filter(appointment_date__date__range=(monday, sunday))
        if self.value() == 'upcoming':
            return queryset.filter(appointment_date__gt=timezone.now())
        return queryset


# queryset.update() : une seule requête SQL, sans save() ni clean() —
# le statut peut donc changer même sur un rendez-vous déjà passé.
@admin.action(description="Confirmer les rendez-vous sélectionnés", permissions=["change"])
def confirm_appointments(modeladmin, request, queryset):
    updated = queryset.update(status=Appointment.Status.CONFIRMED)
    modeladmin.message_user(request, f"{updated} rendez-vous confirmé(s).")


@admin.action(description="Annuler les rendez-vous sélectionnés", permissions=["change"])
def cancel_appointments(modeladmin, request, queryset):
    updated = queryset.update(status=Appointment.Status.CANCELLED)
    modeladmin.message_user(request, f"{updated} rendez-vous annulé(s).")


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('appointment_date', 'doctor', 'patient', 'duration_minutes', 'status')
    list_filter = ('status', 'doctor', DateRangeFilter)
    search_fields = (
        'patient__last_name', 'patient__national_id',
        'doctor__last_name', 'doctor__license_number',
    )
    ordering = ('-appointment_date',)
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ("Participants", {"fields": ("doctor", "patient")}),
        ("Planification", {"fields": ("appointment_date", "duration_minutes", "status")}),
        ("Dossier", {"fields": ("reason", "prescription")}),
        ("Suivi", {"fields": ("created_at", "updated_at")}),
    )
    actions = [confirm_appointments, cancel_appointments]
    # Pour aller plus loin
    autocomplete_fields = ('doctor', 'patient')
    list_per_page = 20
