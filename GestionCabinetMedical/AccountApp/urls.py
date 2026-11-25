from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('medecins/<int:pk>/', views.doctor_detail, name='doctor_detail'),
    path('comptes/inscription/', views.register, name='register'),
]
