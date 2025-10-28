from django.urls import path
from . import views

app_name = 'inventaire'

urlpatterns = [
    path('equipements/', views.EquipementListView.as_view(), name='equipement_list'),
    path('equipements/create/', views.EquipementCreateView.as_view(), name='equipement_create'),
    path('equipements/<int:pk>/update/', views.EquipementUpdateView.as_view(), name='equipement_update'),
    path('equipements/<int:pk>/delete/', views.EquipementDeleteView.as_view(), name='equipement_delete'),

    path('allocations/', views.AllocationEquipementListView.as_view(), name='allocationequipement_list'),
    path('allocations/create/', views.AllocationEquipementCreateView.as_view(), name='allocationequipement_create'),
    path('allocations/<int:pk>/update/', views.AllocationEquipementUpdateView.as_view(), name='allocationequipement_update'),
    path('allocations/<int:pk>/delete/', views.AllocationEquipementDeleteView.as_view(), name='allocationequipement_delete'),
]
