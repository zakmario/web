from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.db.models import Sum
from django.utils import timezone

from AppointmentApp.admin import AppointmentInline
from AppointmentApp.models import Appointment

from .models import Doctor, Patient, Specialty, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    # UserAdmin : le mot de passe est toujours haché.
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Informations personnelles", {
            'classes': ('wide',),
            'fields': ('first_name', 'last_name', 'email'),
        }),
    )


@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    ordering = ('name',)


class AccountModelAdmin(admin.ModelAdmin):
    """Base commune à Doctor et Patient.

    Le mot de passe n'est pas saisi ici (il serait enregistré en clair) : le compte
    est créé avec un mot de passe inutilisable, à définir ensuite depuis la fiche
    du compte dans « Utilisateurs » ou via `python manage.py changepassword`.
    """

    def save_model(self, request, obj, form, change):
        if not change:
            obj.set_unusable_password()
        super().save_model(request, obj, form, change)


@admin.register(Doctor)
class DoctorAdmin(AccountModelAdmin):
    list_display = ('last_name', 'first_name', 'license_number', 'phone', 'confirmed_minutes_today')
    list_filter = ('specialties',)
    search_fields = ('license_number', 'last_name', 'first_name')
    ordering = ('last_name',)
    fieldsets = (
        ("Compte", {'fields': ('username', 'first_name', 'last_name', 'email', 'is_active')}),
        ("Médecin", {'fields': ('license_number', 'phone', 'specialties')}),
    )
    # Pour aller plus loin
    filter_horizontal = ('specialties',)
    list_per_page = 20

    def get_readonly_fields(self, request, obj=None):
        return ('license_number',) if obj else ()

    @admin.display(description="RDV confirmés aujourd'hui (min)")
    def confirmed_minutes_today(self, obj):
        total = obj.appointments.filter(
            status=Appointment.Status.CONFIRMED,
            appointment_date__date=timezone.localdate(),
        ).aggregate(total=Sum('duration_minutes'))['total']
        return total or 0


@admin.register(Patient)
class PatientAdmin(AccountModelAdmin):
    list_display = ('last_name', 'first_name', 'national_id', 'phone', 'birth_date')
    search_fields = ('last_name', 'first_name', 'national_id')
    ordering = ('last_name',)
    fieldsets = (
        ("Compte", {'fields': ('username', 'first_name', 'last_name', 'email', 'is_active')}),
        ("Patient", {'fields': ('national_id', 'phone', 'birth_date')}),
    )
    inlines = [AppointmentInline]
    list_per_page = 20

    def get_readonly_fields(self, request, obj=None):
        return ('national_id',) if obj else ()
