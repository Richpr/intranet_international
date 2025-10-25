# finance/urls.py

from django.urls import path
from . import views
from .views import FinanceDashboardView

app_name = "finance"

urlpatterns = [
    # Tableau de bord financier (dépenses, bilans)
    path("", views.FinanceDashboardView.as_view(), name="dashboard"),
    # Affichage et gestion des structures salariales
    path(
        "structures/",
        views.SalaryStructureListView.as_view(),
        name="salary_structure_list",
    ),
    # Affichage et gestion des dépenses quotidiennes
    path("depenses/", views.DailyExpenseListView.as_view(), name="expense_list"),
    # AJOUTEZ CETTE LIGNE pour le formulaire de création de dépense
    path(
        "depenses/ajouter/",
        views.DailyExpenseCreateView.as_view(),
        name="expense_create",
    ),
    # Enregistrement des Achèvements de Travail (Paie Terrain)
    path(
        "travail/ajouter/",
        views.WorkCompletionCreateView.as_view(),
        name="work_record_create",
    ),
    path("travail/", views.WorkCompletionListView.as_view(), name="work_record_list"),
    path("", FinanceDashboardView.as_view(), name="finance_dashboard"),
]
