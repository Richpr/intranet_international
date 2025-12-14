from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, View
from .models import Certification, PaiementSalaire, Contract, DocumentRequest
from users.models import CustomUser
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from .forms import CertificationForm
from django.http import HttpResponse, HttpResponseForbidden
import uuid
from django.template.loader import render_to_string
from weasyprint import HTML
import datetime
from django.conf import settings
import os
import mimetypes
from pathlib import Path
from urllib.parse import urlparse
import weasyprint
from .utils import generer_reference_sequentielle

def django_weasyprint_url_fetcher(url, *args, **kwargs):
    """
    Custom URL fetcher for WeasyPrint that handles Django static and media files.
    Gère les URL absolues générées lorsque base_url est défini.
    """
    # 1. Handle file:// URLs directly
    if url.startswith('file:'):
        parsed_url = urlparse(url)
        file_path = Path(parsed_url.path)
        if file_path.exists():
            mime_type, encoding = mimetypes.guess_type(file_path.name)
            return {
                'file_obj': open(file_path, 'rb'),
                'mime_type': mime_type,
                'encoding': encoding,
            }

    # 2. Handle Django static files (Correction clé pour base_url absolu)
    if settings.STATIC_URL:
        parsed_url = urlparse(url)
        # On travaille avec le chemin (path) de l'URL absolue (ex: /static/images/logo.png)
        path = parsed_url.path
        
        # Le chemin doit commencer par STATIC_URL (ex: /static/)
        if path.startswith(settings.STATIC_URL):
            # Enlever le préfixe STATIC_URL et forcer la casse en minuscule
            static_path = path.replace(settings.STATIC_URL, '', 1).lower()

            # Utilisation de os.path.join pour construire le chemin absolu de manière fiable
            absolute_path = os.path.join(settings.STATIC_ROOT, static_path) 

            if os.path.exists(absolute_path):
                mime_type, encoding = mimetypes.guess_type(absolute_path)

                return {
                    'file_obj': open(absolute_path, 'rb'),
                    'mime_type': mime_type,
                    'encoding': encoding,
                }

    # 3. Handle Django media files
    if settings.MEDIA_URL and url.startswith(settings.MEDIA_URL):
        media_path = url.replace(settings.MEDIA_URL, '', 1)
        absolute_path = os.path.join(settings.MEDIA_ROOT, media_path)
        if os.path.exists(absolute_path):
            mime_type, encoding = mimetypes.guess_type(absolute_path)
            return {
                'file_obj': open(absolute_path, 'rb'),
                'mime_type': mime_type,
                'encoding': encoding,
            }

    # 4. Fallback to WeasyPrint's default URL fetcher
    return weasyprint.default_url_fetcher(url, *args, **kwargs)

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
        # CORRECTION BASE_URL: Utilisation de l'URL externe fixe
        html = HTML(string=html_string, base_url='http://extranet.ntc-group.org/', url_fetcher=django_weasyprint_url_fetcher)
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

class AttestationPDFView(LoginRequiredMixin, DetailView):
    model = CustomUser
    template_name = 'rh/attestation_pdf.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['employee'] = self.object
        context['year'] = datetime.date.today().year
        context['generation_date'] = datetime.date.today().strftime("%d %B %Y")
        # Generate sequential reference for attestation
        context['reference'] = generer_reference_sequentielle(
            document_type='ATTESTATION',
            code_document_prefix='AT'
        )
        return context

    def render_to_response(self, context, **response_kwargs):
        html_string = render_to_string(self.template_name, context)
        # CORRECTION BASE_URL: Utilisation de l'URL externe fixe
        html = HTML(string=html_string, base_url='http://extranet.ntc-group.org/', url_fetcher=django_weasyprint_url_fetcher)
        pdf = html.write_pdf()
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="attestation_{self.object.username}.pdf"'
        return response

class CertificatTravailPDFView(LoginRequiredMixin, DetailView):
    model = CustomUser
    template_name = 'rh/certificat_travail_pdf.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['employee'] = self.object
        context['contract'] = self.object.contracts.order_by('-start_date').first()
        context['year'] = datetime.date.today().year
        context['generation_date'] = datetime.date.today().strftime("%d %B %Y")
        # Generate sequential reference for certificat de travail
        context['reference'] = generer_reference_sequentielle(
            document_type='CERTIFICAT_TRAVAIL',
            code_document_prefix='CT'
        )
        return context

    def render_to_response(self, context, **response_kwargs):
        html_string = render_to_string(self.template_name, context)
        # CORRECTION BASE_URL: Utilisation de l'URL externe fixe
        html = HTML(string=html_string, base_url='http://extranet.ntc-group.org/', url_fetcher=django_weasyprint_url_fetcher)
        pdf = html.write_pdf()
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="certificat_{self.object.username}.pdf"'
        return response

def generate_work_card(request, employee_id):
    employee = get_object_or_404(CustomUser, id=employee_id)
    contract = Contract.objects.filter(employee=employee).order_by('-start_date').first()
    certifications = Certification.objects.filter(employe=employee)

    context = {
        'employee': employee,
        'contract': contract,
        'certifications': certifications,
    }
    return render(request, 'rh/work_card.html', context)

class RequestDocumentView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        document_type = request.POST.get("document_type")
        if document_type in ["attestation", "certificat"]:
            if not DocumentRequest.objects.filter(employee=request.user, document_type=document_type, status="pending").exists():
                DocumentRequest.objects.create(
                    employee=request.user,
                    document_type=document_type
                )
                messages.success(request, f"Votre demande de {document_type} a été soumise.")
            else:
                messages.warning(request, f"Vous avez déjà une demande de {document_type} en attente.")
        else:
            messages.error(request, "Type de document invalide.")
        
        return redirect("users:profile_update")



class DocumentRequestListView(PermissionRequiredMixin, ListView):
    model = DocumentRequest
    template_name = "rh/documentrequest_list.html"
    context_object_name = "requests"
    permission_required = "rh.view_documentrequest"

    def get_queryset(self):
        return DocumentRequest.objects.filter(status="pending")

class DocumentRequestDetailView(PermissionRequiredMixin, UpdateView):
    model = DocumentRequest
    template_name = "rh/documentrequest_detail.html"
    fields = ["status", "comments"]
    success_url = reverse_lazy("rh:documentrequest_list")
    permission_required = "rh.change_documentrequest"

    def form_valid(self, form):
        instance = form.save(commit=False)
        instance.reviewed_by = self.request.user
        instance.approved_at = datetime.datetime.now()
        instance.save()
        
        # TODO: Trigger email to user with the download link
        
        return super().form_valid(form)

class DownloadDocumentView(LoginRequiredMixin, View):
    def get(self, request, token):
        try:
            # Validate that the token is a valid UUID
            uuid.UUID(token)
        except ValueError:
            return HttpResponseForbidden("Invalid token format.")

        doc_request = get_object_or_404(DocumentRequest, token=token, employee=request.user)

        if doc_request.is_downloaded:
            messages.error(request, "Ce lien de téléchargement a déjà été utilisé.")
            return redirect("users:profile_update")

        if doc_request.status != "approved":
            messages.error(request, "Cette demande n'a pas été approuvée.")
            return redirect("users:profile_update")

        # Generate the PDF based on document_type
        if doc_request.document_type == "attestation":
            view_class = AttestationPDFView
        elif doc_request.document_type == "certificat":
            view_class = CertificatTravailPDFView
        else:
            messages.error(request, "Type de document inconnu.")
            return redirect("users:profile_update")
        
        # We need to instantiate the view to call its methods
        view_instance = view_class()
        view_instance.request = request
        view_instance.kwargs = {'pk': doc_request.employee.pk}
        view_instance.object = doc_request.employee
        context = view_instance.get_context_data()
        
        # We call render_to_response directly
        response = view_instance.render_to_response(context)
        
        # Mark as downloaded and save
        doc_request.is_downloaded = True
        doc_request.save()
        
        return response