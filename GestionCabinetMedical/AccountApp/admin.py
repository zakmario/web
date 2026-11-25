from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Doctor, Patient, Specialty, User

# Doctor et Patient héritent de User : on réutilise UserAdmin pour que le mot de
# passe soit haché à la création et modifiable via le formulaire dédié.


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    pass


@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(Doctor)
class DoctorAdmin(UserAdmin):
    list_display = ('username', 'first_name', 'last_name', 'license_number', 'phone')
    list_filter = ('specialties', 'is_active')
    search_fields = ('username', 'first_name', 'last_name', 'license_number')
    ordering = ('last_name', 'first_name')
    filter_horizontal = ('specialties',)
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ("Informations personnelles", {'fields': ('first_name', 'last_name', 'email', 'phone')}),
        ("Informations professionnelles", {'fields': ('license_number', 'specialties')}),
        ("Statut", {'fields': ('is_active', 'last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'usable_password', 'password1', 'password2'),
        }),
        ("Informations personnelles", {'fields': ('first_name', 'last_name', 'email', 'phone')}),
        ("Informations professionnelles", {'fields': ('license_number', 'specialties')}),
    )

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super().get_readonly_fields(request, obj)
        if obj:  # identifiant métier non modifiable après la création
            return (*readonly_fields, 'license_number')
        return readonly_fields


@admin.register(Patient)
class PatientAdmin(UserAdmin):
    list_display = ('username', 'first_name', 'last_name', 'national_id', 'phone', 'birth_date')
    list_filter = ('is_active',)
    search_fields = ('username', 'first_name', 'last_name', 'national_id')
    ordering = ('last_name', 'first_name')
    filter_horizontal = ()
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ("Informations personnelles", {
            'fields': ('first_name', 'last_name', 'email', 'phone', 'national_id', 'birth_date'),
        }),
        ("Statut", {'fields': ('is_active', 'last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'usable_password', 'password1', 'password2'),
        }),
        ("Informations personnelles", {
            'fields': ('first_name', 'last_name', 'email', 'phone', 'national_id', 'birth_date'),
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super().get_readonly_fields(request, obj)
        if obj:  # identifiant métier non modifiable après la création
            return (*readonly_fields, 'national_id')
        return readonly_fields
