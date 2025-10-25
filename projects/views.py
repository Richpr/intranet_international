# projects/views.py

from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    TemplateView,
)
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    AccessMixin,
    UserPassesTestMixin,
)
from users.models import Country, CustomUser
from django.shortcuts import get_object_or_404, redirect
from django.db import transaction, IntegrityError
from django.db.models import (
    Count,
    Q,
    Avg,
)
from django.db.models.functions import ExtractYear
from django.urls import reverse_lazy, reverse
from datetime import date
from django.core.exceptions import PermissionDenied
from django.contrib import messages  # AJOUT
from .forms import (
    ProjectForm,
    SiteForm,
    TaskForm,
    TaskUpdateForm,
    InspectionForm,
    SiteRadioConfigurationFormset,
)
from django.views.generic import FormView
from .forms import TaskPhotoForm, SimpleTaskUpdateForm
from .models import (
    Project,
    Site,
    Task,
    Inspection,
    TransmissionLink,
    TaskPhoto,
)  # ⬅️ AJOUTER TaskPhoto

# =================================================================
# 1. MIXINS DE CONTRÔLE D'ACCÈS ET D'ISOLATION DE PAYS
# =================================================================


class CountryIsolationMixin(LoginRequiredMixin, AccessMixin):
    """
    Assure que l'utilisateur n'accède qu'aux objets liés aux pays où il est affecté activement.
    """

    def check_country_isolation(self, project):
        """Vérifie que l'utilisateur a accès au pays du projet"""
        user = self.request.user
        if user.is_superuser:
            return True

        if project.country.id not in user.active_country_ids:
            raise PermissionDenied("Vous n'avez pas accès à ce pays.")
        return True

    def get_queryset(self):
        # Utilise la méthode get_queryset de la classe de base (ListView ou DetailView)
        qs = super().get_queryset()
        user = self.request.user

        # 1. Le Superuser voit tout
        if user.is_superuser:
            return qs

        # 2. Filtrer les objets par pays d'affectation
        active_country_ids = user.active_country_ids

        # Le filtre dépend du modèle :
        if self.model == Project:
            return qs.filter(country__id__in=active_country_ids)

        elif self.model == Site:
            return qs.filter(project__country__id__in=active_country_ids)

        elif self.model in [Task, Inspection]:
            return qs.filter(site__project__country__id__in=active_country_ids)

        return qs.none()


# Mixin pour vérifier le rôle de Country Manager ou Superuser
class IsCountryManagerOrSuperuserMixin(UserPassesTestMixin):
    def test_func(self):
        user = self.request.user
        # CORRECTION : user.is_cm est une propriété (retrait des parenthèses)
        return user.is_superuser or user.is_cm


# NOUVEAU Mixin plus strict pour la modification de projet
class IsCMOrSuperuserForProjectMixin(UserPassesTestMixin):
    def test_func(self):
        user = self.request.user
        if user.is_superuser:
            return True

        project_id = self.kwargs.get("pk")
        if not project_id:
            return False
        
        project = get_object_or_404(Project, pk=project_id)
        
        # Seul le CM du pays concerné peut modifier
        is_cm_for_country = user.is_cm and (project.country.id in user.active_country_ids)
        return is_cm_for_country

    def handle_no_permission(self):
        messages.error(self.request, "Seul un Country Manager ou un Administrateur peut modifier un projet.")
        project_pk = self.kwargs.get('pk')
        if project_pk:
            return redirect('projects:project_detail', pk=project_pk)
        return redirect('projects:project_list')


# Mixin pour vérifier le rôle de Project Coordinator ou Superuser
class IsCoordinatorCMOrSuperuserMixin(UserPassesTestMixin):
    def test_func(self):
        user = self.request.user
        if hasattr(self, "project"):
            project = self.project
        elif hasattr(self, "site"):
            project = self.site.project
        else:
            # 💡 CORRECTION DU FALLBACK 💡
            # On cherche d'abord 'pk' (pour ProjectUpdateView), puis 'project_pk'
            project_id = (
                self.kwargs.get("pk")
                or self.kwargs.get("project_pk")
                or self.kwargs.get("site_pk")
            )

            # S'il y a un ID, on essaie de récupérer. Sinon, on lève 404 car la vue est mal configurée.
            if not project_id:
                raise PermissionDenied(
                    "Erreur de configuration de la vue: ID de projet manquant."
                )

            project = get_object_or_404(Project, pk=project_id)

        is_super = user.is_superuser
        is_coordinator = user == project.coordinator
        is_cm_for_country = (
            project.country.id in user.active_country_ids
        )  # Assume CM role checked via active_country_ids

        # DEBUG PRINT (garde pour tests, retire après)
        print(
            f"DEBUG PERM: User={user.username}, Project={project.name}, Super={is_super}, Coordinator={is_coordinator}, CM_country={is_cm_for_country}"
        )

        return is_super or is_coordinator or is_cm_for_country

    def handle_no_permission(self):
        messages.error(
            self.request,
            "Vous n'avez pas la permission pour cette action (vérifiez si vous êtes Coordinateur du projet ou Country Manager du pays concerné).",
        )
        # Redirect vers détail projet ou liste
        project_pk = self.kwargs.get("project_pk") or (
            self.site.project.pk if hasattr(self, "site") else None
        )
        if project_pk:
            return redirect("projects:project_detail", pk=project_pk)
        return redirect("projects:project_list")  # Fallback


# =================================================================
# 2. VUES DE LISTE ET DÉTAIL
# =================================================================


class ProjectListView(CountryIsolationMixin, ListView):
    model = Project
    template_name = "projects/project_list.html"
    context_object_name = "projects"
    paginate_by = 10

    def get_queryset(self):
        user = self.request.user

        if user.is_superuser:
            qs = Project.objects.all()
        else:
            qs = super().get_queryset()

        # --- LOGIQUE DE FILTRAGE ---
        search_query = self.request.GET.get("q", "")
        status_filter = self.request.GET.get("status", "")
        country_filter = self.request.GET.get("country", "")
        coordinator_filter = self.request.GET.get("coordinator", "")
        year_filter = self.request.GET.get("year", "")  # ⬅️ 2. AJOUT
        month_filter = self.request.GET.get("month", "")  # ⬅️ 2. AJOUT

        if search_query:
            qs = qs.filter(
                Q(name__icontains=search_query) | Q(client__name__icontains=search_query)
            )

        if status_filter:
            if status_filter == "active":
                qs = qs.filter(is_active=True, is_completed=False)
            elif status_filter == "completed":
                qs = qs.filter(is_completed=True)
            elif status_filter == "inactive":
                qs = qs.filter(is_active=False)

        if country_filter:
            qs = qs.filter(country__code=country_filter)

        if coordinator_filter:
            qs = qs.filter(coordinator__username=coordinator_filter)

        # ⬅️ 2. AJOUT DE LA LOGIQUE DE FILTRAGE DATE
        if year_filter:
            qs = qs.filter(start_date__year=year_filter)

        if month_filter:
            qs = qs.filter(start_date__month=month_filter)
        # ⬅️ FIN DE L'AJOUT

        # --- ANNOTATIONS ET TRI ---
        qs = (
            qs.select_related("country", "coordinator", "project_type")
            .annotate(
                site_count=Count("sites", distinct=True),
                global_progress=Avg(
                    "sites__progress_percentage",
                    filter=Q(sites__progress_percentage__isnull=False),
                    default=0,
                ),
            )
            .order_by("-start_date")
        )

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # The original 'projects' from context is the PAGINATED slice.
        # To calculate site-wide statistics, we must get the full, un-sliced queryset.
        full_projects_qs = self.get_queryset()

        # Note: We keep context['projects'] (set by super()) for the main page list,
        # but use full_projects_qs for all statistics.

        # Statistiques (All lines below have been corrected to use full_projects_qs)
        context["total_projects"] = full_projects_qs.count()
        # FIX for line 142: Use the fresh queryset to apply the filter
        context["active_projects"] = full_projects_qs.filter(
            is_active=True, is_completed=False
        ).count()

        # Recalculate based on the full queryset (assuming site_count is an annotation)
        context["total_sites"] = sum(project.site_count for project in full_projects_qs)
        context["avg_progress"] = round(
            full_projects_qs.aggregate(avg=Avg("global_progress"))["avg"] or 0, 1
        )

        # ⬇️ 3. LOGIQUE AMÉLIORÉE POUR LES FILTRES ⬇️
        # On utilise un queryset de base (uniquement isolé par pays) pour peupler les filtres
        # afin qu'ils affichent TOUJOURS toutes les options possibles.
        if user.is_superuser:
            base_qs_for_filters = Project.objects.all()
        else:
            base_qs_for_filters = super(ProjectListView, self).get_queryset()

        # CORRECTION CRITIQUE : Filtrer les pays selon l'isolation (using base_qs)
        country_ids = (
            base_qs_for_filters.values_list("country", flat=True).distinct()
        )
        context["countries"] = Country.objects.filter(id__in=country_ids).distinct()

        # CORRECTION : Récupérer les coordinateurs UNIQUES des projets visibles (using base_qs)
        coordinator_ids = base_qs_for_filters.values_list(
            "coordinator", flat=True
        ).distinct()
        context["coordinators"] = CustomUser.objects.filter(
            id__in=coordinator_ids
        ).distinct()

        # 3. AJOUT DES ANNÉES ET MOIS
        context["available_years"] = (
            base_qs_for_filters.annotate(year=ExtractYear("start_date"))
            .values_list("year", flat=True)
            .distinct()
            .order_by("-year")
        )
        context["available_months"] = [
            {"value": i, "name": date(1, i, 1).strftime("%B")} for i in range(1, 13)
        ]
        # ⬆️ FIN DE LA LOGIQUE AMÉLIORÉE ⬆️

        context["is_cm"] = user.is_cm

        # --- AJOUT : Passer les filtres au contexte ---
        context["filters"] = {
            "q": self.request.GET.get("q", ""),
            "status": self.request.GET.get("status", ""),
            "country": self.request.GET.get("country", ""),
            "coordinator": self.request.GET.get("coordinator", ""),
            "year": self.request.GET.get("year", ""),    # ⬅️ AJOUTEZ CETTE LIGNE
            "month": self.request.GET.get("month", ""),
        }
        return context

    def render_to_response(self, context, **response_kwargs):
        if self.request.headers.get("x-requested-with") == "XMLHttpRequest":
            self.template_name = "projects/partials/project_list_partial.html"
        return super().render_to_response(context, **response_kwargs)


class ProjectDetailView(CountryIsolationMixin, DetailView):
    model = Project
    template_name = "projects/project_detail.html"
    context_object_name = "project"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.object
        user = self.request.user

        # Déterminer si c'est un projet Transmission
        is_transmission_project = (
            project.project_type.is_transmission if project.project_type else False
        )
        context["is_transmission_project"] = is_transmission_project

        active_country_ids = user.active_country_ids

        # Récupérer les sites du projet (filtrés par pays actif si pas Superuser)
        if user.is_superuser:
            sites = project.sites.all().prefetch_related(
                "tasks", "inspections", "team_lead"
            )
        else:
            sites = project.sites.filter(
                project__country__id__in=active_country_ids
            ).prefetch_related("tasks", "inspections", "team_lead")

        context["sites"] = sites

        # Calcul du progrès global agrégé des sites
        # Le reste du code de calcul... (omis pour la concision)
        progress_data = sites.aggregate(
            global_progress=Avg(
                "progress_percentage",
                filter=Q(progress_percentage__isnull=False),
                default=0,
            )
        )
        context["global_progress"] = round(progress_data["global_progress"], 2)

        # NOUVELLES STATISTIQUES POUR LE TABLEAU (omis pour la concision)
        context["completed_sites"] = sites.filter(progress_percentage=100).count()
        context["active_tasks"] = Task.objects.filter(
            site__in=sites, status__in=["TO_DO", "IN_PROGRESS"]
        ).count()

        # Team leads pour les filtres du tableau (omis pour la concision)
        context["team_leads"] = CustomUser.objects.filter(
            led_sites__in=sites
        ).distinct()

        # ===============================================
        # 🚀 LOGIQUE DE PERMISSION CORRIGÉE ET AJOUTÉE 🚀
        # ===============================================

        # 1. Le CM est-il le CM du pays du projet ?
        is_cm_for_project_country = user.is_cm and (
            project.country.id in user.active_country_ids
        )

        # 2. L'utilisateur peut GÉRER LE PROJET (éditer, ajouter site/tâche)
        # Condition : Superuser OU (Coordinateur du projet) OU (CM du pays du projet)
        can_manage_project = (
            user.is_superuser
            or user == project.coordinator
            or is_cm_for_project_country
        )

        # Booléens pour les permissions des boutons
        context["can_edit_project"] = can_manage_project  # ⬅️ NOUVELLE PERMISSION CRÉÉE
        context["can_add_site"] = can_manage_project  # ⬅️ LOGIQUE MISE À JOUR
        context["can_add_task"] = can_manage_project  # ⬅️ LOGIQUE MISE À JOUR

        return context


# =================================================================
# 3. VUES DE CRÉATION ET MISE À JOUR
# =================================================================


class SiteCreateView(
    CountryIsolationMixin, IsCoordinatorCMOrSuperuserMixin, CreateView
):
    model = Site
    form_class = SiteForm
    template_name = "projects/site_form.html"

    def dispatch(self, request, *args, **kwargs):
        # Charge et stocke le projet pour toutes les méthodes (post, get, form_valid)
        self.project = get_object_or_404(Project, pk=self.kwargs["project_pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_project(self):
        """Récupère l'objet Project en utilisant le project_pk de l'URL."""
        if not hasattr(self, "_project"):
            project_pk = self.kwargs.get("project_pk")
            self._project = get_object_or_404(Project, pk=project_pk)
        return self._project

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.project

        # Gestion du formset radio
        if self.request.POST:
            context["radio_formset"] = SiteRadioConfigurationFormset(
                self.request.POST, instance=self.object
            )
        else:
            context["radio_formset"] = SiteRadioConfigurationFormset(
                instance=self.object
            )

        return context

    def post(self, request, *args, **kwargs):
        self.object = None
        form = self.get_form()

        if form.is_valid():
            # ✅ CORRECTION : Supprimer la logique de transmission problématique
            # et simplement valider le formulaire
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        context = self.get_context_data()
        radio_formset = context["radio_formset"]

        # 1. Assigner le Projet parent
        project = self.get_project()
        site_instance = form.save(commit=False)
        site_instance.project = project
        site_instance.created_by = self.request.user

        # ✅ CORRECTION : Sauvegarde atomique complète
        with transaction.atomic():
            # Sauvegarder d'abord le site
            site_instance.save()

            # Ensuite sauvegarder le formset
            if radio_formset.is_valid():
                radio_formset.instance = site_instance
                radio_formset.save()
            else:
                # Si le formset n'est pas valide, on retourne l'erreur
                messages.error(
                    self.request,
                    "Erreurs dans la configuration radio. Vérifiez les champs.",
                )
                return self.form_invalid(form)

        messages.success(
            self.request, f"Site '{site_instance.site_id_client}' créé avec succès !"
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("projects:project_detail", kwargs={"pk": self.project.pk})


# VUE POUR LA MODIFICATION DE PROJET (Accès CM/Coordinateur/Superuser)
class ProjectUpdateView(
    CountryIsolationMixin, IsCMOrSuperuserForProjectMixin, UpdateView
):
    model = Project
    form_class = ProjectForm
    template_name = "projects/project_form.html"

    # 💥 CORRECTION CRITIQUE 💥
    def get_object(self, queryset=None):
        # Tente de récupérer l'objet en utilisant le queryset filtré par CountryIsolationMixin.
        # Si le projet 8 n'est pas dans les pays actifs de l'utilisateur, le 404 est levé ici.
        obj = super().get_object(queryset)

        # Stocke l'objet. Cela rend 'hasattr(self, 'project')' VRAI pour le mixin.
        self.project = obj
        return obj

    def get_success_url(self):
        messages.success(
            self.request, f"Projet '{self.object.name}' mis à jour avec succès !"
        )
        return reverse("projects:project_detail", kwargs={"pk": self.object.pk})


class TaskCreateView(
    CountryIsolationMixin, IsCoordinatorCMOrSuperuserMixin, CreateView
):
    model = Task
    form_class = TaskForm
    template_name = "projects/task_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.site = get_object_or_404(Site, pk=self.kwargs["site_pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["site"] = self.site
        return context

    # ⬇️ AJOUT: Passer l'utilisateur au formulaire
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["site"] = self.site
        kwargs["user"] = self.request.user  # ⬅️ AJOUT CRITIQUE
        return kwargs

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.site = self.site
        self.object.created_by = self.request.user  # ⬅️ AJOUT pour la traçabilité
        self.object.save()
        messages.success(
            self.request,
            f"Tâche '{self.object.description}' créée avec succès pour le site {self.site.site_id_client} !",
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("projects:project_detail", kwargs={"pk": self.site.project.pk})


class TaskUpdateView(CountryIsolationMixin, UserPassesTestMixin, UpdateView):
    model = Task
    template_name = "projects/task_update_advanced.html"

    def get_form_class(self):
        """Choisit le formulaire approprié selon le type de tâche"""
        task = self.get_object()

        # Pour SRS et IMK - formulaire simplifié
        if task.task_type and task.task_type.code in ["SRS", "IMK"]:
            return SimpleTaskUpdateForm
        # Pour les autres tâches - formulaire complet
        else:
            return TaskUpdateForm

    def get_form_kwargs(self):
        """Passe l'utilisateur connecté au formulaire"""
        kwargs = super().get_form_kwargs()
        # ⬇️ CORRECTION : Ne passez pas uploaded_by directement
        # Le formulaire l'extrait maintenant dans son __init__
        return kwargs

    def test_func(self):
        """Vérifie que l'utilisateur peut modifier cette tâche"""
        user = self.request.user
        task = self.get_object()

        if user.is_superuser:
            return True
        if user == task.site.project.coordinator:
            return True
        if task.site.project.country.id in user.active_country_ids and user.is_cm:
            return True
        if task.site.team_lead == user:
            return True
        if task.assigned_to == user:
            return True
        return False

    def form_valid(self, form):
        response = super().form_valid(form)

        # Logique de mise à jour du site
        task = form.instance
        site = task.site

        # Le signal post_save gère la mise à jour de site.progress_percentage

        if task.status == "COMPLETED":
            # Logique métier pour les types spécifiques
            if (
                task.task_type
                and task.task_type.code == "SRS"
                and task.result_type
                and task.result_type.code == "DONE"
            ):
                site.status = "SRS_COMPLETED"
                site.save(update_fields=["status"])  # 💡 Mise à jour spécifique
            elif (
                task.task_type
                and task.task_type.code == "IMK"
                and task.result_type
                and task.result_type.code == "DONE"
            ):
                site.status = "IMK_COMPLETED"
                site.save(update_fields=["status"])  # 💡 Mise à jour spécifique

        # ✅ Retrait de site.update_progress() : c'est géré par le signal post_save de Task.

        messages.success(self.request, "Tâche mise à jour avec succès !")
        return response

    def get_success_url(self):
        return reverse(
            "projects:project_detail", kwargs={"pk": self.object.site.project.pk}
        )


class TaskPhotoUploadView(CountryIsolationMixin, UserPassesTestMixin, FormView):
    form_class = TaskPhotoForm
    template_name = "projects/task_photo_upload.html"

    # 💡 AMÉLIORATION : Récupère et stocke la tâche une seule fois
    def dispatch(self, request, *args, **kwargs):
        self.task = get_object_or_404(Task, pk=self.kwargs["pk"])
        # 1. Vérification d'isolation de pays
        self.check_country_isolation(self.task.site.project)
        # 2. Vérification des permissions (test_func)
        return super().dispatch(request, *args, **kwargs)

    def test_func(self):
        """Vérifie que l'utilisateur peut uploader une photo pour cette tâche"""
        user = self.request.user
        task = self.task  # Utilise l'objet stocké
        return (
            user.is_superuser
            or user == task.assigned_to
            or user == task.site.team_lead
            or user == task.site.project.coordinator
            or task.site.project.country.id in user.active_country_ids
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["task"] = self.task  # Utilise l'objet stocké
        return context

    def form_valid(self, form):
        task = self.task

        # 🎯 CORRECTION DÉFINITIVE 3 : Utiliser 'photo' pour récupérer la liste des fichiers
        # Le nom doit correspondre au champ renommé dans forms.py
        photos = self.request.FILES.getlist("photo")
        caption = form.cleaned_data.get("caption", "")

        print(f"Photos trouvées: {len(photos)}")
        print(f"Caption: {caption}")

        if photos:
            try:
                # ... (Logique de sauvegarde)
                with transaction.atomic():
                    for photo in photos:
                        TaskPhoto.objects.create(
                            task=task,
                            photo=photo,  # Ceci est le champ du modèle (correct)
                            caption=caption,
                            uploaded_by=self.request.user,
                        )
                messages.success(
                    self.request, f"{len(photos)} photo(s) ajoutée(s) avec succès !"
                )
                return redirect(self.get_success_url())
            except Exception:
                # ...
                return self.form_invalid(form)
        else:
            # Cette branche gère l'absence de fichiers après la validation réussie
            messages.warning(self.request, "Aucune photo sélectionnée.")
            return self.render_to_response(self.get_context_data(form=form))

    def form_invalid(self, form):
        # Cette branche ne devrait être appelée que si le champ 'caption' a une erreur.
        print("Formulaire invalide. Erreurs:", form.errors)
        messages.error(
            self.request,
            "Erreur dans le formulaire. Vérifiez les champs (légende, etc.).",
        )
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse("projects:task_update", kwargs={"pk": self.kwargs["pk"]})


class InspectionCreateView(CountryIsolationMixin, UserPassesTestMixin, CreateView):
    model = Inspection
    form_class = InspectionForm  # ⬅️ Formulaire externe
    template_name = "projects/inspection_form.html"

    # 💡 Récupération du Site Parent
    def dispatch(self, request, *args, **kwargs):
        self.site = get_object_or_404(Site, pk=kwargs["site_pk"])

        # Vérification d'isolation de pays sur le site
        if (
            not self.request.user.is_superuser
            and self.site.project.country.id not in self.request.user.active_country_ids
        ):
            return self.handle_no_permission()

        return super().dispatch(request, *args, **kwargs)

    # Vérification d'autorisation (CM, Coordinator ou Superuser peuvent créer une inspection)
    def test_func(self):
        user = self.request.user
        # CORRECTION : user.is_cm et user.is_coordinator sont des propriétés (retrait des parenthèses)
        return user.is_superuser or user.is_cm or user.is_coordinator

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["site"] = self.site
        return context

    @transaction.atomic
    def form_valid(self, form):
        # 1. Lie l'inspection au site et définit l'inspecteur
        form.instance.site = self.site
        form.instance.inspector = self.request.user

        response = super().form_valid(form)  # Sauvegarde l'Inspection

        # 2. Mise à jour du résultat de la dernière inspection sur le modèle Site
        self.site.last_inspection_result = self.object.resultat_inspection
        self.site.save(update_fields=["last_inspection_result"])

        return response

    def get_success_url(self):
        return reverse("projects:project_detail", kwargs={"pk": self.site.project.pk})


class TeamLeadTasksView(CountryIsolationMixin, ListView):
    model = Task
    template_name = "projects/team_lead_tasks.html"
    context_object_name = "tasks"

    def get_queryset(self):
        user = self.request.user

        # Base filters for active tasks
        active_status_filter = Q(status__in=["TO_DO", "IN_PROGRESS", "QC_PENDING"])

        # CountryIsolationMixin is already applied via super().get_queryset()
        qs = super().get_queryset()

        # Filter for tasks assigned to the user or on sites they lead
        user_task_filter = Q(assigned_to=user) | Q(site__team_lead=user)

        queryset = (
            qs.filter(active_status_filter & user_task_filter)
            .distinct()
            .select_related(
                "assigned_to",
                "site__team_lead",
                "site__project__country",
                "task_type",
            )
            .order_by("site__site_id_client", "due_date")
        )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context["today"] = date.today()

        # Role information for the template
        context["is_team_lead"] = user.is_team_lead
        context["is_field_team"] = user.is_field_team

        # For debug section
        context["user_groups"] = [g.name for g in user.groups.all()]
        active_country_ids = user.active_country_ids
        context["sites_managed_count"] = Site.objects.filter(
            team_lead=user, project__country__id__in=active_country_ids
        ).count()
        context["assigned_tasks_count"] = Task.objects.filter(
            assigned_to=user, site__project__country__id__in=active_country_ids
        ).count()

        return context


class SiteUpdateView(CountryIsolationMixin, UpdateView):
    model = Site
    form_class = SiteForm
    template_name = "projects/site_form.html"  # Réutilise le template

    def get_success_url(self):
        # Redirection vers le détail du projet après la mise à jour
        return reverse_lazy(
            "projects:project_detail", kwargs={"pk": self.object.project.pk}
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.object.project

        # Gestion du Formset (Radio Configuration) pour la modification
        if self.request.POST:
            context["radio_formset"] = SiteRadioConfigurationFormset(
                self.request.POST, instance=self.object
            )
        else:
            context["radio_formset"] = SiteRadioConfigurationFormset(
                instance=self.object
            )

        return context

    def form_valid(self, form):
        context = self.get_context_data()
        radio_formset = context.get("radio_formset")
        # 💥 AJOUT CRITIQUE : Assigner l'utilisateur qui fait la modification
        form.instance.updated_by = self.request.user

        with transaction.atomic():
            self.object = form.save()  # Sauvegarde du Site

            if radio_formset and radio_formset.is_valid():
                radio_formset.instance = self.object
                radio_formset.save()
            elif radio_formset:
                # Si le formset n'est pas valide, on retourne l'erreur
                return self.form_invalid(form)

            messages.success(
                self.request,
                f"Le site {self.object.site_id_client} a été mis à jour avec succès.",
            )
            return super().form_valid(form)


class SiteDetailView(CountryIsolationMixin, DetailView):
    model = Site
    template_name = "projects/site_detail.html"
    context_object_name = "site"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        site = self.object

        # Récupérer toutes les tâches du site
        tasks = site.tasks.all().select_related("assigned_to", "task_type")
        context["tasks"] = tasks

        # Récupérer toutes les inspections du site
        inspections = site.inspections.all().select_related("inspector")
        context["inspections"] = inspections

        # Statistiques du site
        context["completed_tasks"] = tasks.filter(status="COMPLETED").count()
        context["active_tasks"] = tasks.filter(
            status__in=["TO_DO", "IN_PROGRESS"]
        ).count()
        context["total_tasks"] = tasks.count()

        # Dernière inspection
        context["last_inspection"] = inspections.order_by("-date_inspection").first()

        return context


class TransmissionLinkCreateView(CountryIsolationMixin, TemplateView):

    # Le modèle n'est pas nécessaire ici, car nous gérons la sauvegarde dans post()
    # Le 'form_class' n'est pas nécessaire non plus.

    # 📌 Définir explicitement les classes de formulaires utilisées
    form_a_class = SiteForm
    form_b_class = SiteForm

    template_name = (
        "projects/transmission_link_form.html"  # Assurez-vous que c'est le bon template
    )
    permission_required = ("projects.add_transmissionlink",)

    # Assurez-vous d'avoir une méthode pour récupérer le projet parent
    def get_project(self):
        return get_object_or_404(Project, pk=self.kwargs["project_pk"])

    # --- Gestion du GET (Affichage) ---
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.get_project()

        # CORRECTION : Utiliser les mêmes noms que dans le template
        if self.request.method == "POST":
            context["form_a"] = SiteForm(
                self.request.POST,
                prefix="site_a",
                user=self.request.user,
                project=project,
            )
            context["form_b"] = SiteForm(
                self.request.POST,
                prefix="site_b",
                user=self.request.user,
                project=project,
            )
        else:
            context["form_a"] = SiteForm(
                prefix="site_a", user=self.request.user, project=project
            )
            context["form_b"] = SiteForm(
                prefix="site_b", user=self.request.user, project=project
            )

        context["project"] = project
        return context

    # --- Gestion du POST (Soumission) ---
    def post(self, request, *args, **kwargs):
        project = self.get_project()

        # CORRECTION : Utiliser request.POST au lieu de self.request.POST
        form_a = SiteForm(
            request.POST, prefix="site_a", user=request.user, project=project
        )
        form_b = SiteForm(
            request.POST, prefix="site_b", user=request.user, project=project
        )

        if form_a.is_valid() and form_b.is_valid():
            try:
                with transaction.atomic():
                    # Sauvegarde Site A
                    site_a = form_a.save(commit=False)
                    site_a.project = project
                    site_a.created_by = request.user
                    site_a.is_transmission_a_site = True
                    site_a.save()

                    # Sauvegarde Site B
                    site_b = form_b.save(commit=False)
                    site_b.project = project
                    site_b.created_by = request.user
                    site_b.is_transmission_b_site = True
                    site_b.save()

                    # Génération du link_id
                    site_a_id = site_a.site_id_client.upper().strip()
                    site_b_id = site_b.site_id_client.upper().strip()
                    link_id = f"{site_a_id}-{site_b_id}"

                    # Création de la liaison
                    TransmissionLink.objects.create(
                        link_id=link_id, site_a=site_a, site_b=site_b
                    )

                    messages.success(
                        request, f"Liaison Transmission ({link_id}) créée avec succès !"
                    )
                    return redirect(self.get_success_url())

            except IntegrityError:
                messages.error(
                    request,
                    f"Erreur : Le lien '{link_id}' existe déjà. Vérifiez les IDs clients.",
                )
            except Exception as e:
                messages.error(request, f"Erreur inattendue : {e}")

        # En cas d'erreur, retourner le contexte avec les erreurs
        context = self.get_context_data()
        context["form_a"] = form_a
        context["form_b"] = form_b
        return self.render_to_response(context)

    def get_success_url(self):
        # Rediriger vers la page de détail du projet (ou tout autre endroit logique)
        return reverse("projects:project_detail", kwargs={"pk": self.get_project().pk})


class ProjectCreateView(
    CountryIsolationMixin, IsCountryManagerOrSuperuserMixin, CreateView
):
    """
    Vue pour la création d'un nouveau projet.
    Accessible uniquement par les Country Managers ou Superusers.
    """

    model = Project
    form_class = ProjectForm
    template_name = "projects/project_form.html"

    def get_form_kwargs(self):
        """Passe l'utilisateur au formulaire pour filtrer les Country Managers."""
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        # La Country est implicitement définie dans le form (qui filtre sur les pays du CM)
        messages.success(self.request, "Le projet a été créé avec succès.")
        return super().form_valid(form)

    def get_success_url(self):
        # Redirige vers la liste des projets après la création
        return reverse("projects:project_list")


class TaskReportView(CountryIsolationMixin, DetailView):
    model = Task
    template_name = "projects/task_report.html"
    context_object_name = "task"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        task = self.get_object()
        # Assurer l'isolation des pays
        self.check_country_isolation(task.site.project)
        context["site"] = task.site
        context["project"] = task.site.project
        context["photos"] = task.task_images.all()
        return context


class ProjectTableView(CountryIsolationMixin, ListView):
    model = Project
    template_name = "projects/project_table.html"
    context_object_name = "projects"

    def get_queryset(self):
        qs = super().get_queryset().select_related("country", "coordinator", "client")

        # Annoter avec des informations agrégées
        qs = qs.annotate(
            site_count=Count("sites", distinct=True),
            global_progress=Avg(
                "sites__progress_percentage",
                filter=Q(sites__progress_percentage__isnull=False),
                default=0,
            ),
        ).order_by("-start_date")

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        projects = context["projects"]

        # 💡 NOUVEAU : 1. Récupérer les PKs des projets visibles.
        # Ceci est une opération sûre sur un QuerySet annoté.
        project_pks = projects.values_list("pk", flat=True)

        # Statistiques (Votre code existant)
        context["total_projects"] = projects.count()
        context["active_projects"] = projects.filter(
            is_active=True, is_completed=False
        ).count()
        context["total_sites"] = sum(project.site_count for project in projects)
        context["avg_progress"] = round(
            projects.aggregate(avg=Avg("global_progress"))["avg"] or 0, 1
        )

        # ✅ CORRECTION PAYS (Évite le TypeError)
        # 2. Utiliser les PKs pour créer un nouveau QuerySet simple sur le modèle Project,
        # puis faire le distinct sur les pays.
        country_pks = (
            Project.objects.filter(pk__in=project_pks)
            .values_list("country__pk", flat=True)
            .distinct()
        )

        # 3. Filtrer les objets Country
        context["countries"] = Country.objects.filter(pk__in=country_pks).order_by(
            "name"
        )

        # ✅ CORRECTION COORDINATEURS (Évite le TypeError)
        # Même logique pour les coordinateurs.
        coordinator_ids = (
            Project.objects.filter(pk__in=project_pks)
            .values_list("coordinator", flat=True)
            .distinct()
        )

        context["coordinators"] = CustomUser.objects.filter(
            id__in=coordinator_ids
        ).distinct()


        # ⬇️ AJOUT DE LA LOGIQUE ANNÉE/MOIS ⬇️
        
        # 4. Récupérer les années distinctes en utilisant la même logique
        context["available_years"] = (
            Project.objects.filter(pk__in=project_pks)
            .annotate(year=ExtractYear("start_date"))
            .values_list("year", flat=True)
            .distinct()
            .order_by("-year")
        )

        # 5. Ajouter les mois
        context["available_months"] = [
            {"value": i, "name": date(1, i, 1).strftime("%B")} for i in range(1, 13)
        ]
        
        # ⬆️ FIN DE L'AJOUT ⬆️

        context["is_cm"] = user.is_cm
        return context
