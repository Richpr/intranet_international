# finance/views.py

# --- Imports Django ---
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DeleteView
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML

# --- Imports Locaux (de cette app) ---
from .models import Depense, Revenu, SalaryStructure, ObligationFiscale
from .forms import DepenseForm, WorkCompletionForm, RevenuForm

# --- Imports Externes (d'autres apps) ---
from projects.models import WorkCompletionRecord
from core.mixins import TeamLeadOrCoordinatorRequiredMixin, ExpenseManagementMixin


# ==========================================================
# MIXIN POUR L'ISOLATION DES DONNÉES PAR PAYS
# ==========================================================

class FinanceCountryIsolationMixin(LoginRequiredMixin):
    """
    Mixin pour isoler les requêtes financières aux pays actifs de l'utilisateur.
    S'applique à toutes les ListView.
    """
    def get_queryset(self):
        # Récupère le queryset de base (ex: Depense.objects.all())
        qs = super().get_queryset() 
        user = self.request.user

        # Le Superuser voit tout
        if user.is_superuser:
            return qs

        # Récupère les pays actifs de l'utilisateur (depuis users/models.py)
        active_country_ids = user.active_country_ids

        # Applique le filtre basé sur le modèle utilisé par la vue
        if self.model == SalaryStructure:
            return qs.filter(country__id__in=active_country_ids)
        
        if self.model == Depense:
            return qs.filter(projet_associe__country__id__in=active_country_ids)
        
        if self.model == Revenu:
            return qs.filter(projet_facture__country__id__in=active_country_ids)
        
        if self.model == WorkCompletionRecord:
            # CORRECTION : Le chemin correct est Tâche -> Site -> Projet -> Pays
            return qs.filter(task__site__project__country__id__in=active_country_ids)
        
        # Par défaut, ne rien retourner si le modèle n'est pas géré
        return qs.none()

# ==========================================================
# VUES PRINCIPALES (Dashboard et Listes)
# ==========================================================

class FinanceDashboardView(LoginRequiredMixin, TemplateView):
    """
    CORRIGÉ : Utilise TemplateView car c'est une page d'accueil, 
    pas une liste d'un modèle spécifique.
    """
    template_name = "finance/finance_dashboard.html"

    def get_context_data(self, **kwargs):
        """Ajoute des statistiques au tableau de bord."""
        context = super().get_context_data(**kwargs)
        active_countries = self.request.user.active_country_ids
        
        # Ajoute des statistiques (filtrées par pays)
        context['total_depenses'] = Depense.objects.filter(
            projet_associe__country__id__in=active_countries
        ).count()
        context['total_revenus'] = Revenu.objects.filter(
            projet_facture__country__id__in=active_countries
        ).count()
        context['total_structures'] = SalaryStructure.objects.filter(
            country__id__in=active_countries
        ).count()
        return context

def depense_pdf_view(request, depense_id):
    depense = get_object_or_404(Depense, id=depense_id)
    html_string = render_to_string('finance/depense_pdf.html', {'depense': depense})
    html = HTML(string=html_string, base_url=request.build_absolute_uri())
    pdf = html.write_pdf()
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="depense_{depense.id}.pdf"'
    return response

class DepenseListView(FinanceCountryIsolationMixin, ListView):
    """Liste les dépenses (filtrées par le Mixin)."""
    model = Depense
    template_name = "finance/expense_list.html" # Correspond à vos templates
    context_object_name = "expenses" # Correspond à vos templates


class RevenuListView(FinanceCountryIsolationMixin, ListView):
    """Liste les revenus (filtrés par le Mixin)."""
    model = Revenu
    template_name = "finance/revenu_list.html"
    context_object_name = "revenus"


class SalaryStructureListView(FinanceCountryIsolationMixin, ListView):
    """Liste les structures salariales (filtrées par le Mixin)."""
    model = SalaryStructure
    template_name = "finance/salary_structure_list.html"
    context_object_name = "structures"


class WorkRecordListView(FinanceCountryIsolationMixin, ListView):
    """
    Vue pour lister tous les enregistrements de travail (Paie Terrain).
    Filtrée par le Mixin.
    """
    model = WorkCompletionRecord
    template_name = "finance/work_completion_list.html"
    context_object_name = "work_records"
    
    def get_queryset(self):
        # Le Mixin gère le filtre, on ajoute juste le tri
        qs = super().get_queryset()
        return qs.order_by('-date')

# ==========================================================
# VUES DE CRÉATION (Formulaires)
# ==========================================================

from django.shortcuts import render, get_object_or_404

class DepenseCreateView(ExpenseManagementMixin, CreateView):
    """Vue pour créer une nouvelle dépense."""
    model = Depense
    form_class = DepenseForm
    template_name = "finance/expense_form.html"
    success_url = reverse_lazy("finance:expense_list") # Retourne à la liste

    def form_valid(self, form):
        # Associe automatiquement la dépense à l'utilisateur qui la déclare
        form.instance.employe_declarant = self.request.user 
        return super().form_valid(form)

class RevenuCreateView(LoginRequiredMixin, CreateView):
    """Vue pour créer un nouveau revenu."""
    model = Revenu
    form_class = RevenuForm
    template_name = "finance/revenu_form.html"
    success_url = reverse_lazy("finance:revenu_list")


class WorkRecordCreateView(LoginRequiredMixin, CreateView):
    """Vue pour créer un nouvel enregistrement de travail (heures/achèvement)."""
    model = WorkCompletionRecord
    form_class = WorkCompletionForm
    template_name = "finance/work_completion_form.html"
    success_url = reverse_lazy("finance:work_record_list") # Retourne à la liste

    def form_valid(self, form):
        # Associe automatiquement l'enregistrement à l'utilisateur qui le crée
        form.instance.created_by = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        # Ajoute le pays actif au contexte (basé sur votre template)
        context = super().get_context_data(**kwargs)
        active_country = self.request.user.active_countries_objects.first()
        if active_country:
            context['country_code'] = active_country.code
        else:
            context['country_code'] = "N/A"
        return context

class ObligationFiscaleListView(LoginRequiredMixin, ListView):
    model = ObligationFiscale
    template_name = "finance/obligationfiscale_list.html"
    context_object_name = "obligations"

class ObligationFiscaleCreateView(PermissionRequiredMixin, CreateView):
    model = ObligationFiscale
    template_name = "finance/obligationfiscale_form.html"
    fields = '__all__'
    success_url = reverse_lazy("finance:obligationfiscale_list")
    permission_required = 'finance.add_obligationfiscale'

class ObligationFiscaleUpdateView(PermissionRequiredMixin, UpdateView):
    model = ObligationFiscale
    template_name = "finance/obligationfiscale_form.html"
    fields = '__all__'
    success_url = reverse_lazy("finance:obligationfiscale_list")
    permission_required = 'finance.change_obligationfiscale'

class ObligationFiscaleDeleteView(PermissionRequiredMixin, DeleteView):
    model = ObligationFiscale
    template_name = "finance/obligationfiscale_confirm_delete.html"
    success_url = reverse_lazy("finance:obligationfiscale_list")
    permission_required = 'finance.delete_obligationfiscale'        