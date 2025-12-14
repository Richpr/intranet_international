from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import Equipement, AllocationEquipement
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from .forms import EquipementForm

class EquipementListView(LoginRequiredMixin, ListView):
    model = Equipement
    template_name = 'inventaire/equipement_list.html'
    context_object_name = 'equipements'

class EquipementCreateView(PermissionRequiredMixin, CreateView):
    model = Equipement
    form_class = EquipementForm
    template_name = 'inventaire/equipement_form.html'
    success_url = reverse_lazy('inventaire:equipement_list')
    permission_required = 'inventaire.add_equipement'

class EquipementUpdateView(PermissionRequiredMixin, UpdateView):
    model = Equipement
    form_class = EquipementForm
    template_name = 'inventaire/equipement_form.html'
    success_url = reverse_lazy('inventaire:equipement_list')
    permission_required = 'inventaire.change_equipement'

class EquipementDeleteView(PermissionRequiredMixin, DeleteView):
    model = Equipement
    template_name = 'inventaire/equipement_confirm_delete.html'
    success_url = reverse_lazy('inventaire:equipement_list')
    permission_required = 'inventaire.delete_equipement'


class AllocationEquipementListView(LoginRequiredMixin, ListView):
    model = AllocationEquipement
    template_name = 'inventaire/allocationequipement_list.html'
    context_object_name = 'allocations'

class AllocationEquipementCreateView(PermissionRequiredMixin, CreateView):
    model = AllocationEquipement
    template_name = 'inventaire/allocationequipement_form.html'
    fields = '__all__'
    success_url = reverse_lazy('inventaire:allocationequipement_list')
    permission_required = 'inventaire.add_allocationequipement'

class AllocationEquipementUpdateView(PermissionRequiredMixin, UpdateView):
    model = AllocationEquipement
    template_name = 'inventaire/allocationequipement_form.html'
    fields = '__all__'
    success_url = reverse_lazy('inventaire:allocationequipement_list')
    permission_required = 'inventaire.change_allocationequipement'

class AllocationEquipementDeleteView(PermissionRequiredMixin, DeleteView):
    model = AllocationEquipement
    template_name = 'inventaire/allocationequipement_confirm_delete.html'
    success_url = reverse_lazy('inventaire:allocationequipement_list')
    permission_required = 'inventaire.delete_allocationequipement'
