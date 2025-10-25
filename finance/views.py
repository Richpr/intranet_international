# finance/views.py

from django.views.generic import TemplateView, ListView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from projects.views import CountryIsolationMixin
from .models import SalaryStructure, DailyExpense, WorkCompletionRecord
from .forms import DailyExpenseForm, WorkCompletionForm
from django.urls import reverse_lazy


# =================================================================
# 1. Mixin de Vérification de Groupe (Accès à l'app Finance)
# =================================================================
class FinanceGroupRequiredMixin(UserPassesTestMixin):
    """
    Vérifie si l'utilisateur est Superuser OU appartient à un groupe autorisé à accéder au module Finance.
    """

    # ⚠️ Ces noms doivent correspondre EXACTEMENT aux Groupes que vous avez créés dans /admin/
    allowed_groups = [
        "Country_Manager",
        "Project_Coordinator",
        "Finance_User",
        "Finance_Admin",
    ]

    def test_func(self):
        user = self.request.user

        # 1. Superuser voit tout
        if user.is_superuser:
            return True

        # 2. Vérifie l'appartenance à un des groupes définis
        return user.groups.filter(name__in=self.allowed_groups).exists()

    # Optionnel: Gérer la permission refusée (rediriger vers l'accueil ou 403)
    # def handle_no_permission(self):
    #     return redirect('home') # Nécessite l'import de redirect


# =================================================================
# Mixins de Permission Spécifiques à la Finance
# =================================================================


class FinanceAccessMixin(CountryIsolationMixin):
    """
    Mixin qui combine la connexion obligatoire et le filtrage par pays.
    Il surcharge get_queryset pour gérer les chemins de relation complexes
    pour les différents modèles du module finance en sautant le filtre par défaut du parent.
    """

    def get_queryset(self):
        # CORRECTION CRUCIALE : On remonte la MRO au-dessus de CountryIsolationMixin
        # pour obtenir le queryset de base (WorkCompletionRecord.objects.all())
        qs = super(CountryIsolationMixin, self).get_queryset()

        user = self.request.user

        if user.is_superuser:
            return qs

        active_country_ids = user.active_countries

        # 2. Appliquer la logique de filtrage spécifique au modèle
        if self.model == SalaryStructure or self.model == DailyExpense:
            return qs.filter(country__id__in=active_country_ids)

        elif self.model == WorkCompletionRecord:
            # Chemin indirect : task -> site -> project -> country
            return qs.filter(task__site__project__country__id__in=active_country_ids)

        return qs.none()


# =================================================================
# Vues d'Affichage
# =================================================================


class FinanceDashboardView(LoginRequiredMixin, TemplateView):
    """
    Tableau de bord de base de la finance.
    """

    # 🌟 CORRECTION DE L'ERREUR ImproperlyConfigured 🌟

    template_name = "finance/finance_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Vous pouvez ajouter ici des données de synthèse futures
        return context


class SalaryStructureListView(FinanceAccessMixin, ListView):
    """
    Liste des structures salariales, filtrée par les pays de l'utilisateur.
    """

    model = SalaryStructure
    template_name = "finance/salary_structure_list.html"
    context_object_name = "structures"


class DailyExpenseListView(FinanceAccessMixin, ListView):
    """
    Liste des dépenses, filtrée par les pays de l'utilisateur.
    """

    model = DailyExpense
    template_name = "finance/expense_list.html"
    context_object_name = "expenses"


# =================================================================
# Vue de Création (Pour les Dépenses)
# =================================================================


class DailyExpenseCreateView(FinanceAccessMixin, CreateView):
    """
    Formulaire de saisie d'une nouvelle dépense.
    """

    model = DailyExpense
    form_class = DailyExpenseForm
    success_url = reverse_lazy("finance:expense_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        # Assigner l'utilisateur courant comme celui qui a créé l'enregistrement
        form.instance.created_by = self.request.user
        return super().form_valid(form)


# =================================================================
# Vues d'Achèvement de Travail (Paie/Terrain)
# =================================================================


class WorkCompletionListView(FinanceAccessMixin, ListView):
    """
    Liste des achèvements de travail, filtrée via FinanceAccessMixin.
    """

    model = WorkCompletionRecord
    context_object_name = "work_records"
    template_name = "finance/work_completion_list.html"

    def get_queryset(self):
        # Le mixin d'isolation filtre déjà par pays actif
        # Utilisation de select_related pour charger l'utilisateur, la tâche et le créateur en une seule requête.
        return (
            super()
            .get_queryset()
            .select_related("user", "task", "created_by")
            .order_by("-date", "-created_at")
        )


class WorkCompletionCreateView(FinanceAccessMixin, CreateView):
    model = WorkCompletionRecord
    form_class = WorkCompletionForm
    success_url = reverse_lazy("finance:work_record_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        user = self.request.user

        country_id = None

        # NOTE : Récupération du premier pays actif de l'utilisateur
        active_assignment = user.assignments.filter(is_active=True).first()
        if active_assignment:
            country_id = active_assignment.country_id

        # Passe l'ID du pays au formulaire (pour filtrer Tâches et Employés)
        kwargs["country_id"] = country_id
        return kwargs

    def form_valid(self, form):
        # Assigner l'utilisateur courant comme celui qui a créé l'enregistrement
        form.instance.created_by = self.request.user
        return super().form_valid(form)
