from django.urls import path
from . import views

app_name = 'rh'

urlpatterns = [
    path('certifications/', views.CertificationListView.as_view(), name='certification_list'),
    path('certifications/create/', views.CertificationCreateView.as_view(), name='certification_create'),
    path('certifications/<int:pk>/update/', views.CertificationUpdateView.as_view(), name='certification_update'),
    path('certifications/<int:pk>/delete/', views.CertificationDeleteView.as_view(), name='certification_delete'),

    path('paiements-salaires/', views.PaiementSalaireListView.as_view(), name='paiementsalaire_list'),
    path('paiements-salaires/create/', views.PaiementSalaireCreateView.as_view(), name='paiementsalaire_create'),
    path('paiements-salaires/<int:pk>/update/', views.PaiementSalaireUpdateView.as_view(), name='paiementsalaire_update'),
    path('paiements-salaires/<int:pk>/delete/', views.PaiementSalaireDeleteView.as_view(), name='paiementsalaire_delete'),

    path('employees/', views.EmployeeListView.as_view(), name='employee_list'),
    path('employees/<int:pk>/', views.EmployeeDetailView.as_view(), name='employee_detail'),
]
