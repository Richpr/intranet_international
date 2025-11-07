from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from .models import Certification, PaiementSalaire, Contract
from users.models import CustomUser
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from .forms import CertificationForm
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML

class ContractListView(LoginRequiredMixin, ListView):
    model = Contract
    template_name = 'rh/contract_list.html'
    context_object_name = 'contracts'

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.is_cm:
            return Contract.objects.all()
        return Contract.objects.filter(employee=user)

class ContractDetailView(LoginRequiredMixin, DetailView):
    model = Contract
    template_name = 'rh/contract_detail.html'
    context_object_name = 'contract'

class ContractPdfView(LoginRequiredMixin, DetailView):
    model = Contract
    template_name = 'rh/contract_pdf.html'

    def render_to_response(self, context, **response_kwargs):
        html_string = render_to_string(self.template_name, context)
        html = HTML(string=html_string)
        pdf = html.write_pdf()
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="contract_{self.object.pk}.pdf"'
        return response

class ContractSignView(LoginRequiredMixin, UpdateView):
    model = Contract
    fields = ['is_signed']
    template_name = 'rh/contract_sign.html'

    def get_success_url(self):
        return reverse_lazy('rh:contract_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        if not self.object.is_signed:
            form.instance.is_signed = True
        return super().form_valid(form)


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
