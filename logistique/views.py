from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from .models import Vehicule, MissionLogistique
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML

class MissionLogistiqueDetailView(LoginRequiredMixin, DetailView):
    model = MissionLogistique
    template_name = 'logistique/missionlogistique_detail.html'
    context_object_name = 'mission'

class MissionLetterPdfView(LoginRequiredMixin, DetailView):
    model = MissionLogistique
    template_name = 'logistique/mission_letter_pdf.html'

    def render_to_response(self, context, **response_kwargs):
        html_string = render_to_string(self.template_name, context)
        html = HTML(string=html_string)
        pdf = html.write_pdf()
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="mission_letter_{self.object.pk}.pdf"'
        return response

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