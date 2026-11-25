"""
URL configuration for GestionCabinetMedical project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from AccountApp.api import DoctorViewSet, PatientViewSet, SpecialtyViewSet
from AppointmentApp.api import AppointmentViewSet

router = DefaultRouter()
router.register('specialties', SpecialtyViewSet)
router.register('doctors', DoctorViewSet, basename='doctor')
router.register('patients', PatientViewSet)
router.register('appointments', AppointmentViewSet, basename='appointment')

admin.site.site_header = "Cabinet Médical - Administration"
admin.site.site_title = "Cabinet Médical"
admin.site.index_title = "Back-office"

urlpatterns = [
    # Front-office
    path('', include('AccountApp.urls')),
    path('rendez-vous/', include('AppointmentApp.urls')),
    path('comptes/', include('django.contrib.auth.urls')),
    # Back-office
    path('admin/', admin.site.urls),
    # API REST
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
