from django.urls import path

from . import views

urlpatterns = [
    path('', views.appointment_list, name='appointment_list'),
    path('nouveau/', views.appointment_create, name='appointment_create'),
    path('<int:pk>/annuler/', views.appointment_cancel, name='appointment_cancel'),
    path('<int:pk>/confirmer/', views.appointment_confirm, name='appointment_confirm'),
    path('<int:pk>/ordonnance/', views.appointment_prescription, name='appointment_prescription'),
]
