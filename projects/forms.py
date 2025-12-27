# projects/forms.py

from django import forms
from django.forms import (
    ModelForm,
    inlineformset_factory,
)
from django.forms.widgets import DateInput
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


from .models import (
    Project,
    Site,
    Task,
    Inspection,
    SiteRadioConfiguration,
    RadioType,
    SiteType,
    InstallationType,
    TaskResultType,
    TaskType,
    TaskPhoto,
    UninstallationReport,
    UninstalledEquipment,
)
from users.models import CustomUser, Role


# -----------------------------------------------------------------------------
# 1. Project Form
# -----------------------------------------------------------------------------
class ProjectForm(ModelForm):
    class Meta:
        model = Project
        exclude = (
            "progress_percentage",
            "created_by",
            "updated_by",
        )
        widgets = {
            "start_date": DateInput(attrs={"type": "date"}),
            "end_date": DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        # ✅ Le 'user' est extrait correctement ici
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

                # CORRECTION : Utilise le queryset du champ country
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
        # MISE À JOUR : Exclure les champs gérés automatiquement
        exclude = (
            "progress_percentage",
            "created_by",
            "updated_by",
            "is_transmission_a_site",
            "is_transmission_b_site",
        )
        widgets = {
            "start_date": DateInput(attrs={"type": "date"}),
            "end_date": DateInput(attrs={"type": "date"}),
        }

    
    def __init__(self, *args, **kwargs):
        # 1. EXTRAIRE les arguments personnalisés
        project = kwargs.pop("project", None)
        user = kwargs.pop("user", None) 
        site_instance = kwargs.get("instance")

        if not project and site_instance:
            project = site_instance.project

        # 2. Appeler le constructeur parent
        super().__init__(*args, **kwargs)

        # 3. Logique de filtrage générale (S'applique TOUJOURS)
        self.fields["site_type"].queryset = SiteType.objects.filter(is_active=True)
        self.fields["installation_type"].queryset = InstallationType.objects.filter(is_active=True)

        # --- SÉCURITÉ : Ces lignes doivent être ICI, hors du "if project" ---
        # Cela garantit que même sans projet, le formulaire bloque si c'est vide
        self.fields["installation_type"].required = True
        self.fields["site_type"].required = True
        
        self.fields["installation_type"].error_messages = {
            'required': "Le type d'installation est obligatoire pour enregistrer un site."
        }
        self.fields["site_type"].error_messages = {
            'required': "Veuillez sélectionner un type de site."
        }
        # ------------------------------------------------------------------

        # 4. Logique spécifique au Projet
        if project:
            team_lead_role = Role.objects.filter(name="Team Lead").first()
            
            # Filtrage des Team Leads
            team_leads_in_country = CustomUser.objects.filter(
                assignments__country=project.country,
                assignments__is_active=True,
                assignments__end_date__isnull=True,
            )
            
            if team_lead_role:
                team_leads_in_country = team_leads_in_country.filter(assignments__role=team_lead_role)

            self.fields["team_lead"].queryset = team_leads_in_country.distinct()
            self.fields["team_lead"].label = _(f"Team Lead (pour {project.country.code})")
            self.fields["team_lead"].required = False
# -----------------------------------------------------------------------------
# 3. SiteRadioConfiguration Formset
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


# Crée le Formset.
SiteRadioConfigurationFormset = inlineformset_factory(
    Site,
    SiteRadioConfiguration,
    form=SiteRadioConfigurationForm,
    extra=1,
    can_delete=True,
    max_num=10,  # Limite à 10 types de radio par site
)


# -----------------------------------------------------------------------------
# 4. Task Form
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
        # 🟢 CORRECTION PRINCIPALE : Extraction de l'argument 'user'
        user = kwargs.pop("user", None) # noqa: F841 - Extrait l'utilisateur, même s'il n'est pas utilisé après
        
        super().__init__(*args, **kwargs)

        self.fields["task_type"].queryset = TaskType.objects.filter(is_active=True)

        if site:
            # Récupérer tous les utilisateurs actifs du pays du projet
            assigned_users_in_country = CustomUser.objects.filter(
                assignments__country=site.project.country,
                assignments__is_active=True,
                assignments__end_date__isnull=True,
            ).distinct()

            self.fields["assigned_to"].queryset = assigned_users_in_country


class TaskUpdateForm(ModelForm):
    class Meta:
        model = Task
        fields = [
            "task_type",
            "assigned_to",
            "status",
            "due_date",
            "progress_percentage",
            "result_type",
            "description",
            "ticket_number",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "due_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        self.uploaded_by = kwargs.pop("uploaded_by", None)
        country = kwargs.pop("country", None)
        super().__init__(*args, **kwargs)

        self.fields["task_type"].disabled = True

        if self.instance and self.instance.task_type:
            self.fields["result_type"].queryset = self.instance.task_type.allowed_result_types.all()
        else:
            self.fields["result_type"].queryset = TaskResultType.objects.none()

        if self.instance.status != "COMPLETED":
            self.fields["result_type"].widget = forms.HiddenInput()

        if self.instance and self.instance.site and self.instance.site.project:
            assigned_users_in_country = CustomUser.objects.filter(
                assignments__country=self.instance.site.project.country,
                assignments__is_active=True,
                assignments__end_date__isnull=True,
            ).distinct()
            self.fields["assigned_to"].queryset = assigned_users_in_country.order_by('first_name', 'last_name')

        self.fields["assigned_to"].label = _("Assigner à (Employé)")
        self.fields["assigned_to"].empty_label = _("--- Sélectionner un membre de l'équipe ---")
        self.fields["assigned_to"].label_from_instance = lambda obj: (
            f"{obj.get_full_name()} ({obj.username})" if obj.get_full_name() else obj.username
        )

        for field in self.fields.values():
            if not isinstance(field.widget, forms.HiddenInput):
                existing_classes = field.widget.attrs.get("class", "")
                field.widget.attrs.update({"class": f"{existing_classes} form-control".strip()})

    def save(self, commit=True):
        task = super().save(commit=False)
        if task.status == "COMPLETED" and task.result_type and not task.completion_date:
            task.completion_date = timezone.now()
        if commit:
            task.save()
        return task


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
        fields = ["assigned_to", "status", "progress_percentage", "description", "ticket_number"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        self.uploaded_by = kwargs.pop("uploaded_by", None)
        country = kwargs.pop("country", None)
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.site and self.instance.site.project:
            assigned_users_in_country = CustomUser.objects.filter(
                assignments__country=self.instance.site.project.country,
                assignments__is_active=True,
                assignments__end_date__isnull=True,
            ).distinct()
            self.fields["assigned_to"].queryset = assigned_users_in_country.order_by('first_name', 'last_name')
            self.fields["assigned_to"].label = _("Assigner à (Employé)")
            self.fields["assigned_to"].empty_label = _("--- Sélectionner un membre de l'équipe ---")
            self.fields["assigned_to"].label_from_instance = lambda obj: (
                f"{obj.get_full_name()} ({obj.username})" if obj.get_full_name() else obj.username
            )

        if self.instance.result_type:
            if self.instance.result_type.code == "DONE":
                self.fields["result_done"].initial = "DONE"
            elif self.instance.result_type.code == "NOT_DONE":
                self.fields["result_done"].initial = "NOT_DONE"

    def save(self, commit=True):
        task = super().save(commit=False)
        result_done = self.cleaned_data.get("result_done")
        if result_done:
            result_type, created = TaskResultType.objects.get_or_create(
                code=result_done,
                defaults={
                    "name": "Terminé" if result_done == "DONE" else "Non Terminé",
                    "is_success": result_done == "DONE",
                },
            )
            task.result_type = result_type
            if result_done == "DONE" and task.status != "COMPLETED":
                task.status = "COMPLETED"
                task.progress_percentage = 100
                from django.utils import timezone
                task.completion_date = timezone.now()
        if commit:
            task.save()
        return task



class MultipleFileInput(
    forms.FileInput
):
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
# -----------------------------------------------------------------------------
class InspectionForm(ModelForm):

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





# -----------------------------------------------------------------------------
# 7. Formulaires de Rapport de Désinstallation (NOUVEAU)
# -----------------------------------------------------------------------------

class UninstallationReportForm(ModelForm):
    """
    Formulaire principal pour le rapport de désinstallation.
    Ne gère que les champs du rapport lui-même.
    """
    class Meta:
        model = UninstallationReport
        fields = ['storage_location']
        widgets = {
            'storage_location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _("Entrepôt, magasin, etc.")}),
        }
        labels = {
            'storage_location': _("Lieu de dépôt du matériel"),
        }


class UninstalledEquipmentForm(ModelForm):
    """
    Formulaire pour *une seule ligne* d'équipement désinstallé.
    """
    class Meta:
        model = UninstalledEquipment
        fields = ['equipment_name', 'quantity', 'serial_number', 'product_code', 'comment']
        widgets = {
            'equipment_name': forms.TextInput(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'serial_number': forms.TextInput(attrs={'class': 'form-control'}),
            'product_code': forms.TextInput(attrs={'class': 'form-control'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 1}),
        }

# Crée le Formset.
UninstalledEquipmentFormset = inlineformset_factory(
    UninstallationReport,  # Modèle parent
    UninstalledEquipment,  # Modèle enfant
    form=UninstalledEquipmentForm,
    extra=1,  # Commence avec 1 formulaire vide
    can_delete=True,
    min_num=0, # Autorise de n'avoir aucun équipement
)