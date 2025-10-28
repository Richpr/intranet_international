from django.urls import path
from . import views

app_name = 'logistique'

urlpatterns = [
    path('vehicules/', views.VehiculeListView.as_view(), name='vehicule_list'),
    path('vehicules/create/', views.VehiculeCreateView.as_view(), name='vehicule_create'),
    path('vehicules/<int:pk>/update/', views.VehiculeUpdateView.as_view(), name='vehicule_update'),
    path('vehicules/<int:pk>/delete/', views.VehiculeDeleteView.as_view(), name='vehicule_delete'),

    path('missions/', views.MissionLogistiqueListView.as_view(), name='missionlogistique_list'),
    path('missions/create/', views.MissionLogistiqueCreateView.as_view(), name='missionlogistique_create'),
    path('missions/<int:pk>/update/', views.MissionLogistiqueUpdateView.as_view(), name='missionlogistique_update'),
    path('missions/<int:pk>/delete/', views.MissionLogistiqueDeleteView.as_view(), name='missionlogistique_delete'),
]
