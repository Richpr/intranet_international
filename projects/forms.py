# projects/forms.py

from django import forms
from django.forms import (
    ModelForm,
    inlineformset_factory,
)  # 💡 AJOUT : Import de inlineformset_factory
from django.forms.widgets import DateInput
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db.models import Q


from .models import (
    Project,
    Site,
    Task,
    Inspection,
    SiteRadioConfiguration,
    RadioType,
    SiteType,
    InstallationType,
    TaskResultType,  # ⬅️ AJOUTEZ CET IMPORT
    TaskType,  # ⬅️ AJOUTEZ AUSSI TaskType SI NÉCESSAIRE
    TaskPhoto,
)
from users.models import CustomUser, Role  # Import des modèles externes


# -----------------------------------------------------------------------------
# 1. Project Form
# (Pas de changement)
# -----------------------------------------------------------------------------
class ProjectForm(ModelForm):
    # ... (Code existant)
    class Meta:
        model = Project
        exclude = (
            "progress_percentage",
            "created_by",  # ⬅️ NE DOIT PAS APPARAÎTRE
            "updated_by",  # ⬅️ NE DOIT PAS APPARAÎTRE
        )
        widgets = {
            "start_date": DateInput(attrs={"type": "date"}),
            "end_date": DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        if user:
            # Récupère le rôle 'Country Manager'
            cm_role = Role.objects.filter(
                name__in=["Country Manager", "Country_Manager"]
            ).first()

            if cm_role:
                # Isole les IDs de pays où l'utilisateur est CM actif
                active_cm_country_ids = user.assignments.filter(
                    role=cm_role, is_active=True, end_date__isnull=True
                ).values_list("country__id", flat=True)

                # ✅ CORRECTION : Utilisez le queryset du champ country au lieu de user.country_set
                self.fields["country"].queryset = self.fields[
                    "country"
                ].queryset.filter(id__in=active_cm_country_ids)

            # Filtre les Coordonnateurs
            coordinator_role = Role.objects.filter(
                name__in=["Project Coordinator", "Project_Coordinator"]
            ).first()
            if coordinator_role:
                coordinator_ids = (
                    CustomUser.objects.filter(
                        assignments__role=coordinator_role,
                        assignments__is_active=True,
                        assignments__end_date__isnull=True,
                    )
                    .distinct()
                    .values_list("id", flat=True)
                )

                self.fields["coordinator"].queryset = CustomUser.objects.filter(
                    id__in=coordinator_ids
                )


# -----------------------------------------------------------------------------
# 2. Site Form (Mise à jour)
# -----------------------------------------------------------------------------
class SiteForm(ModelForm):

    class Meta:
        model = Site
        # 💡 MISE À JOUR : Exclure les champs gérés automatiquement
        exclude = (
            "progress_percentage",
            "created_by",  # ⬅️ NE DOIT PAS APPARAÎTRE
            "updated_by",  # ⬅️ NE DOIT PAS APPARAÎTRE
            "is_transmission_a_site",  # Probablement déjà exclu (si vous l'utilisez)
            "is_transmission_b_site",  # Probablement déjà exclu (si vous l'utilisez)
        )
        widgets = {
            # ... (widgets existants) ...
            "start_date": DateInput(attrs={"type": "date"}),
            "end_date": DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        # 1. EXTRAIRE les arguments personnalisés (user, project) AVANT le super().
        project = kwargs.pop("project", None)  # On extrait 'project' ici
        user = kwargs.pop("user", None)

        site_instance = kwargs.get("instance")

        # Si 'project' n'a pas été passé directement, mais que nous avons une instance,
        # on essaie de le récupérer de l'instance.
        if not project and site_instance:
            project = site_instance.project

        # 2. Appeler le constructeur parent (kwargs est maintenant "propre")
        super().__init__(*args, **kwargs)

        # 3. Utiliser les variables extraites pour la logique de filtrage
        # 💡 AJOUT : Limiter les options aux types actifs

        self.fields["site_type"].queryset = SiteType.objects.filter(is_active=True)
        self.fields["installation_type"].queryset = InstallationType.objects.filter(
            is_active=True
        )

        if project:
            # 1. Team Lead: Filtrer les Team Leads pour le pays du projet
            team_lead_role = Role.objects.filter(name="Team Lead").first()
            if team_lead_role:
                team_leads_in_country = CustomUser.objects.filter(
                    assignments__country=project.country,
                    assignments__role=team_lead_role,
                    assignments__is_active=True,
                    assignments__end_date__isnull=True,
                ).distinct()
            else:
                # Si le rôle 'Team Lead' n'existe pas, permettre tous les utilisateurs actifs du pays
                team_leads_in_country = CustomUser.objects.filter(
                    assignments__country=project.country,
                    assignments__is_active=True,
                    assignments__end_date__isnull=True,
                ).distinct()

            self.fields["team_lead"].queryset = team_leads_in_country
            self.fields["team_lead"].label = _(
                f"Team Lead (pour {project.country.code})"
            )

        # 2. Rendre optionnels les champs de référence technique pour la création rapide
        # Ces champs sont déjà null=True/blank=True dans models.py, donc ils sont facultatifs ici par défaut.
        # On peut expliciter si on voulait surcharger le comportement du modèle.


# -----------------------------------------------------------------------------
# 3. SiteRadioConfiguration Formset (NOUVEAU)
# -----------------------------------------------------------------------------
class SiteRadioConfigurationForm(ModelForm):
    """
    Formulaire pour la ligne de configuration Radio.
    """

    radio_type = forms.ModelChoiceField(
        queryset=RadioType.objects.filter(is_active=True),
        label=_("Modèle de Radio"),
        widget=forms.Select(attrs={"class": "form-select radio-type-select"}),
    )

    quantity = forms.IntegerField(
        min_value=1,
        initial=1,
        widget=forms.NumberInput(
            attrs={"class": "form-control quantity-input", "min": "1"}
        ),
    )

    class Meta:
        model = SiteRadioConfiguration
        fields = ["radio_type", "quantity"]


# Crée le Formset. max_num=10 limite le nombre de radios qu'on peut ajouter
SiteRadioConfigurationFormset = inlineformset_factory(
    Site,
    SiteRadioConfiguration,
    form=SiteRadioConfigurationForm,
    extra=1,
    can_delete=True,
    max_num=10,  # Limite à 10 types de radio par site
)


# -----------------------------------------------------------------------------
# 4. Task Form (Pas de changement, car TaskUpdateForm est géré séparément)
# -----------------------------------------------------------------------------
class TaskForm(ModelForm):
    class Meta:
        model = Task
        fields = [
            "task_type",
            "description",
            "assigned_to",
            "due_date",
            "is_paid_relevant",
            "expected_duration_hours",
        ]
        widgets = {
            "due_date": DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(
                attrs={
                    "rows": 2,
                    "placeholder": _("Description complémentaire (optionnel)"),
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        site = kwargs.pop("site", None)
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        self.fields["task_type"].queryset = TaskType.objects.filter(is_active=True)

        if site:
            # Récupérer tous les utilisateurs actifs du pays du projet
            assigned_users_in_country = CustomUser.objects.filter(
                assignments__country=site.project.country,
                assignments__is_active=True,
                assignments__end_date__isnull=True,
            ).distinct()

            # ⬇️ CORRECTION: Filtrer pour n'inclure que les Team Leads et Field Teams
            team_lead_role = Role.objects.filter(name="Team Lead").first()
            field_team_role = Role.objects.filter(name="Field Team").first()

            if team_lead_role or field_team_role:
                role_filter = Q()
                if team_lead_role:
                    role_filter |= Q(assignments__role=team_lead_role)
                if field_team_role:
                    role_filter |= Q(assignments__role=field_team_role)

                assigned_users_in_country = assigned_users_in_country.filter(
                    role_filter
                )

            self.fields["assigned_to"].queryset = assigned_users_in_country


class TaskUpdateForm(ModelForm):
    class Meta:
        model = Task
        fields = [
            "task_type",
            "status",
            "progress_percentage",
            "result_type",
            "description",
            "ticket_number",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        # ⬇️ CORRECTION : Extraire uploaded_by avant d'appeler super()
        self.uploaded_by = kwargs.pop("uploaded_by", None)
        super().__init__(*args, **kwargs)

        # 👇 AJOUTEZ CETTE LIGNE POUR VERROUILLER LE CHAMP
        self.fields["task_type"].disabled = True
        # 👆 FIN DE L'AJOUT

        self.fields["task_type"].queryset = TaskType.objects.filter(is_active=True)

        if self.instance.task_type:
            self.fields["result_type"].queryset = (
                self.instance.task_type.allowed_result_types.all()
            )
        else:
            self.fields["result_type"].queryset = TaskResultType.objects.none()

        if self.instance.status != "COMPLETED":
            self.fields["result_type"].widget = forms.HiddenInput()

    def save(self, commit=True):
        task = super().save(commit=False)

        if task.status == "COMPLETED" and task.result_type and not task.completion_date:
            task.completion_date = timezone.now()

        if commit:
            task.save()

        return task


class MultipleFileInput(
    forms.FileInput
):  # Gardez cette classe (ou celle basée sur ClearableFileInput, au choix)
    def __init__(self, attrs=None):
        super().__init__(attrs)
        if attrs is not None:
            self.attrs = attrs.copy()
        else:
            self.attrs = {}
        self.attrs["multiple"] = True

    def value_from_datadict(self, data, files, name):
        """Récupère la liste de fichiers et retourne None si la liste est vide."""

        # 1. Tente de récupérer la liste de fichiers
        file_list = files.getlist(name)

        # 2. Si la liste est vide, retourne None.
        if not file_list:
            # RETOURNER None EST CRITIQUE pour que required=False fonctionne
            return None

        # 3. Sinon, retourne la liste de fichiers.
        return file_list


class TaskPhotoForm(forms.ModelForm):
    """
    Formulaire pour l'upload de photos multiples.
    Le champ 'photo' est géré manuellement dans le template et la vue.
    """

    class Meta:
        model = TaskPhoto
        fields = ["caption"]
        widgets = {
            "caption": forms.Textarea(
                attrs={"rows": 2, "placeholder": _("Légende ou commentaire rapide...")}
            ),
        }


# -----------------------------------------------------------------------------
# 6. Inspection Form
# (Pas de changement)
# -----------------------------------------------------------------------------
class InspectionForm(ModelForm):

    # ... (Code existant)
    class Meta:
        model = Inspection
        exclude = (
            "site",
            "inspector",
        )
        widgets = {
            "date_inspection": DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["rapport_photos_url"].required = False


class SimpleTaskUpdateForm(ModelForm):
    """Formulaire simplifié pour les tâches SRS/IMK qui n'ont besoin que de DONE/NOT_DONE"""

    result_done = forms.ChoiceField(
        choices=(
            ("", "---------"),
            ("DONE", "✅ Terminé (DONE)"),
            ("NOT_DONE", "❌ Non Terminé (NOT_DONE)"),
        ),
        required=False,
        label=_("Résultat"),
    )

    class Meta:
        model = Task
        fields = ["status", "progress_percentage", "description", "ticket_number"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        # ⬇️ CORRECTION : Extraire uploaded_by avant d'appeler super()
        self.uploaded_by = kwargs.pop("uploaded_by", None)
        super().__init__(*args, **kwargs)

        # Pré-remplir le champ result_done si un résultat existe
        if self.instance.result_type:
            if self.instance.result_type.code == "DONE":
                self.fields["result_done"].initial = "DONE"
            elif self.instance.result_type.code == "NOT_DONE":
                self.fields["result_done"].initial = "NOT_DONE"

    def save(self, commit=True):
        task = super().save(commit=False)

        # Gérer le résultat DONE/NOT_DONE
        result_done = self.cleaned_data.get("result_done")
        if result_done:
            # ⬇️ CORRECTION : TaskResultType est maintenant importé
            result_type, created = TaskResultType.objects.get_or_create(
                code=result_done,
                defaults={
                    "name": "Terminé" if result_done == "DONE" else "Non Terminé",
                    "is_success": result_done == "DONE",
                },
            )
            task.result_type = result_type

            # Si marqué comme DONE, compléter automatiquement la tâche
            if result_done == "DONE" and task.status != "COMPLETED":
                task.status = "COMPLETED"
                task.progress_percentage = 100
                from django.utils import timezone

                task.completion_date = timezone.now()

        if commit:
            task.save()

        return task
