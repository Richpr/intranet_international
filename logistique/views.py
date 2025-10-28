from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import Vehicule, MissionLogistique
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

class VehiculeListView(LoginRequiredMixin, ListView):
    model = Vehicule
    template_name = 'logistique/vehicule_list.html'
    context_object_name = 'vehicules'

class VehiculeCreateView(PermissionRequiredMixin, CreateView):
    model = Vehicule
    template_name = 'logistique/vehicule_form.html'
    fields = '__all__'
    success_url = reverse_lazy('logistique:vehicule_list')
    permission_required = 'logistique.add_vehicule'

class VehiculeUpdateView(PermissionRequiredMixin, UpdateView):
    model = Vehicule
    template_name = 'logistique/vehicule_form.html'
    fields = '__all__'
    success_url = reverse_lazy('logistique:vehicule_list')
    permission_required = 'logistique.change_vehicule'

class VehiculeDeleteView(PermissionRequiredMixin, DeleteView):
    model = Vehicule
    template_name = 'logistique/vehicule_confirm_delete.html'
    success_url = reverse_lazy('logistique:vehicule_list')
    permission_required = 'logistique.delete_vehicule'


class MissionLogistiqueListView(LoginRequiredMixin, ListView):
    model = MissionLogistique
    template_name = 'logistique/missionlogistique_list.html'
    context_object_name = 'missions'

class MissionLogistiqueCreateView(PermissionRequiredMixin, CreateView):
    model = MissionLogistique
    template_name = 'logistique/missionlogistique_form.html'
    fields = '__all__'
    success_url = reverse_lazy('logistique:missionlogistique_list')
    permission_required = 'logistique.add_missionlogistique'

class MissionLogistiqueUpdateView(PermissionRequiredMixin, UpdateView):
    model = MissionLogistique
    template_name = 'logistique/missionlogistique_form.html'
    fields = '__all__'
    success_url = reverse_lazy('logistique:missionlogistique_list')
    permission_required = 'logistique.change_missionlogistique'

class MissionLogistiqueDeleteView(PermissionRequiredMixin, DeleteView):
    model = MissionLogistique
    template_name = 'logistique/missionlogistique_confirm_delete.html'
    success_url = reverse_lazy('logistique:missionlogistique_list')
    permission_required = 'logistique.delete_missionlogistique'