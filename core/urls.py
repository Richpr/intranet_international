# core/urls.py

from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Définit la vue 'dashboard_view' comme page d'accueil de l'app 'core'
    # Ligne 10 (corrigée)
    path('', views.HomeView.as_view(), name='dashboard'),
]