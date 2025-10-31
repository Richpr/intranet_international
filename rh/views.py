from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from .models import Certification, PaiementSalaire
from users.models import CustomUser
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from .forms import CertificationForm

class CertificationListView(LoginRequiredMixin, ListView):
    model = Certification
    template_name = 'rh/certification_list.html'
    context_object_name = 'certifications'

class CertificationCreateView(PermissionRequiredMixin, CreateView):
    model = Certification
    form_class = CertificationForm
    template_name = 'rh/certification_form.html'
    success_url = reverse_lazy('rh:certification_list')
    permission_required = 'rh.add_certification'

class CertificationUpdateView(PermissionRequiredMixin, UpdateView):
    model = Certification
    form_class = CertificationForm
    template_name = 'rh/certification_form.html'
    success_url = reverse_lazy('rh:certification_list')
    permission_required = 'rh.change_certification'

class CertificationDeleteView(PermissionRequiredMixin, DeleteView):
    model = Certification
    template_name = 'rh/certification_confirm_delete.html'
    success_url = reverse_lazy('rh:certification_list')
    permission_required = 'rh.delete_certification'


class PaiementSalaireListView(LoginRequiredMixin, ListView):
    model = PaiementSalaire
    template_name = 'rh/paiementsalaire_list.html'
    context_object_name = 'paiements_salaires'

    def get_queryset(self):
        user = self.request.user
        if user.groups.filter(name='Gestionnaire RH').exists() or user.is_superuser:
            return PaiementSalaire.objects.all()
        return PaiementSalaire.objects.filter(employe=user)

class PaiementSalaireCreateView(PermissionRequiredMixin, CreateView):
    model = PaiementSalaire
    template_name = 'rh/paiementsalaire_form.html'
    fields = '__all__'
    success_url = reverse_lazy('rh:paiementsalaire_list')
    permission_required = 'rh.add_paiementsalaire'

class PaiementSalaireUpdateView(PermissionRequiredMixin, UpdateView):
    model = PaiementSalaire
    template_name = 'rh/paiementsalaire_form.html'
    fields = '__all__'
    success_url = reverse_lazy('rh:paiementsalaire_list')
    permission_required = 'rh.change_paiementsalaire'

class PaiementSalaireDeleteView(PermissionRequiredMixin, DeleteView):

    model = PaiementSalaire

    template_name = 'rh/paiementsalaire_confirm_delete.html'

    success_url = reverse_lazy('rh:paiementsalaire_list')

    permission_required = 'rh.delete_paiementsalaire'





class EmployeeListView(LoginRequiredMixin, ListView):

    model = CustomUser

    template_name = 'rh/employee_list.html'

    context_object_name = 'employees'



class EmployeeDetailView(LoginRequiredMixin, DetailView):

    model = CustomUser

    template_name = 'rh/employee_detail.html'

    context_object_name = 'employee'


class EmployeePerformanceView(LoginRequiredMixin, ListView):
    model = CustomUser
    template_name = 'rh/employee_performance.html'
    context_object_name = 'employees'

    def get_queryset(self):
        users = CustomUser.objects.all()
        
        # Trier les utilisateurs en Python
        def sort_key(user):
            if user.main_role == 'Field Team':
                return user.technician_completion_rate()
            elif user.main_role == 'Team Lead':
                return user.team_lead_success_rate()
            elif user.main_role == 'Coordinateur de Projet':
                return user.coordinator_on_time_completion_rate()
            else:
                return 0

        sorted_users = sorted(users, key=sort_key, reverse=True)
        return sorted_users
