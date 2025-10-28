# finance/urls.py
from django.urls import path
from . import views

app_name = "finance"

urlpatterns = [
    # 1. Dashboard
    path("", views.FinanceDashboardView.as_view(), name="finance_dashboard"),

    # 2. Dépenses (Expenses)
    path("depenses/", views.DepenseListView.as_view(), name="expense_list"), # <-- Corrigé (un seul 't')
    path("depenses/creer/", views.DepenseCreateView.as_view(), name="expense_create"), # <-- AJOUTÉ
    path("depenses/<int:depense_id>/pdf/", views.depense_pdf_view, name="depense_pdf"),

    # 3. Revenus
    path("revenus/", views.RevenuListView.as_view(), name="revenu_list"),
    path("revenus/creer/", views.RevenuCreateView.as_view(), name="revenu_create"),

    # 4. Structures Salariales
    path("salary-structures/", views.SalaryStructureListView.as_view(), name="salary_structure_list"),
    
    # 5. Paie Terrain (Work Records)
    path("paie-terrain/", views.WorkRecordListView.as_view(), name="work_record_list"), # <-- AJOUTÉ
    path("paie-terrain/creer/", views.WorkRecordCreateView.as_view(), name="work_record_create"), # <-- AJOUTÉ

    # 6. Obligations Fiscales
    path("obligations-fiscales/", views.ObligationFiscaleListView.as_view(), name="obligationfiscale_list"),
    path("obligations-fiscales/creer/", views.ObligationFiscaleCreateView.as_view(), name="obligationfiscale_create"),
    path("obligations-fiscales/<int:pk>/modifier/", views.ObligationFiscaleUpdateView.as_view(), name="obligationfiscale_update"),
    path("obligations-fiscales/<int:pk>/supprimer/", views.ObligationFiscaleDeleteView.as_view(), name="obligationfiscale_delete"),
]