# /home/rich/intranet_international/projects/models.py

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from core.models import Departement
from django.db.models import Avg
from datetime import date
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal  # Pour garantir la précision des calculs


# =================================================================
# CHOIX EXISTANTS
# =================================================================
# CHOIX pour le type d'Inspection
INSPECTION_TYPE_CHOICES = (
    ("PRE_PAT", _("Pré-Validation Interne (PRE-PAT)")),
    ("ATP", _("Acceptation Client (ATP)")),
)

# CHOIX pour le résultat de l'Inspection
INSPECTION_RESULT_CHOICES = (
    ("FTR", _("First Time Right (FTR)")),
    ("NFTR", _("Not First Time Right (NFTR)")),
)

# CHOIX pour le statut de la Tâche
TASK_STATUS_CHOICES = (
    ("TO_DO", _("À Faire")),
    ("IN_PROGRESS", _("En Cours")),
    ("QC_PENDING", _("Contrôle Qualité (QC)")),
    ("COMPLETED", _("Terminée")),
    ("BLOCKED", _("Bloquée")),
)

# NOUVEAUX CHOIX pour la Catégorisation des Tâches (pour l'automatisation des statuts de Site)
TASK_TYPE_CHOICES = (
    ("INSTALLATION", _("Installation")),
    ("INTEGRATION", _("Intégration")),
    ("SRS", _("SRS")),
    ("IMK", _("IMK")),
    # Un seul type 'EHS' pour l'instant, les EHS multiples (EHS1, EHS2) seront gérés par la création de tâches distinctes
    ("EHS", _("EHS")),
    ("QA", _("QA")),
    ("ATP", _("ATP")),
    ("OTHER", _("Autre")),
)

PROJECT_STATUS_CHOICES = (
    ("PREPARATION", _("En préparation")),
    ("IN_PROGRESS", _("En cours")),
    ("COMPLETED", _("Terminé")),
    ("INVOICED", _("Facturé")),
    ("PAID", _("Payé")),
)


# =================================================================
# MODÈLE ABSTRAIT POUR LA TRAÇABILITÉ (NOUVEAU)
# =================================================================


class TraceabilityModel(models.Model):
    """
    Modèle abstrait pour ajouter automatiquement les champs
    created_by et updated_by à un modèle.
    """

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        editable=False,
        related_name="%(class)s_created",  # Permet le reverse lookup sur plusieurs modèles
        verbose_name=_("Créé par"),
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        editable=False,
        related_name="%(class)s_updated",
        verbose_name=_("Mis à jour par"),
    )

    class Meta:
        abstract = True  # 💡 CLÉ : Ne pas créer de table pour ce modèle


# =================================================================
# 1. NOUVEAUX Modèles de Référence (Lookup Models) gérés par l'Admin
# DÉFINIS EN PREMIER POUR ÉVITER LES ERREURS DE RÉFÉRENCE
# =================================================================
class BaseLookupModel(models.Model):
    """Classe abstraite pour tous les modèles de référence (listes déroulantes de l'admin)."""

    name = models.CharField(
        max_length=100, unique=True, verbose_name=_("Nom de la référence")
    )
    is_active = models.BooleanField(default=True, verbose_name=_("Actif"))

    class Meta:
        abstract = True
        ordering = ["name"]

    def __str__(self):
        return self.name


class SitePhase(BaseLookupModel):
    class Meta(BaseLookupModel.Meta):
        verbose_name = _("Phase de Site")
        verbose_name_plural = _("Phases de Sites")


class Batch(BaseLookupModel):
    class Meta(BaseLookupModel.Meta):
        verbose_name = _("Batch de Site")
        verbose_name_plural = _("Batches de Sites")


class AntennaType(BaseLookupModel):
    class Meta(BaseLookupModel.Meta):
        verbose_name = _("Type d'Antenne")
        verbose_name_plural = _("Types d'Antennes")


class EnclosureType(BaseLookupModel):
    class Meta(BaseLookupModel.Meta):
        verbose_name = _("Type d'Enclosure (Boîtier)")
        verbose_name_plural = _("Types d'Enclosures (Boîtiers)")


class BBMLType(BaseLookupModel):
    class Meta(BaseLookupModel.Meta):
        verbose_name = _("BB / ML")
        verbose_name_plural = _("BB / ML")


class RadioType(BaseLookupModel):
    class Meta(BaseLookupModel.Meta):
        verbose_name = _("Modèle de Radio")
        verbose_name_plural = _("Modèles de Radio")


class Client(BaseLookupModel):
    class Meta(BaseLookupModel.Meta):
        verbose_name = _("Client")
        verbose_name_plural = _("Clients")


class SiteType(models.Model):
    name = models.CharField(
        max_length=100, unique=True, verbose_name=_("Nom du Type de Site")
    )
    is_active = models.BooleanField(default=True, verbose_name=_("Est Actif"))

    class Meta:
        verbose_name = _("Type de Site (Rooftop/Greenfield)")
        verbose_name_plural = _("Types de Sites")
        ordering = ("name",)

    def __str__(self):
        return self.name


class InstallationType(models.Model):
    name = models.CharField(
        max_length=100, unique=True, verbose_name=_("Nom du Type d'Installation")
    )
    is_active = models.BooleanField(default=True, verbose_name=_("Est Actif"))

    class Meta:
        verbose_name = _("Type d'Installation (RAN/Transmission)")
        verbose_name_plural = _("Types d'Installation")
        ordering = ("name",)

    def __str__(self):
        return self.name


class TaskResultType(models.Model):
    """Types de résultats possibles (FTR, NFTR, DONE, NOT_DONE, etc.)"""

    name = models.CharField(max_length=50, verbose_name=_("Nom du résultat"))
    code = models.CharField(max_length=20, unique=True, verbose_name=_("Code"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    is_success = models.BooleanField(default=True, verbose_name=_("Est un succès"))

    class Meta:
        verbose_name = _("Type de Résultat")
        verbose_name_plural = _("Types de Résultats")
        ordering = ["name"]

    def __str__(self):
        return self.name


class TaskType(models.Model):
    CATEGORY_CHOICES = (
        ("PREPARATION", _("Préparation")),
        ("INSTALLATION", _("Installation")),
        ("TESTING", _("Tests et Validation")),
        ("DOCUMENTATION", _("Documentation")),
        ("SAFETY", _("Sécurité")),
        ("CLOSURE", _("Clôture")),
    )

    name = models.CharField(max_length=100, verbose_name=_("Nom du type de tâche"))
    code = models.CharField(max_length=20, unique=True, verbose_name=_("Code unique"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    category = models.CharField(
        max_length=50, choices=CATEGORY_CHOICES, default="INSTALLATION"
    )

    # NOUVEAU: Types de résultats autorisés pour ce type de tâche
    allowed_result_types = models.ManyToManyField(
        TaskResultType,
        blank=True,
        verbose_name=_("Types de résultats autorisés"),
        help_text=_("Types de résultats que l'utilisateur peut sélectionner"),
    )

    requires_photos = models.BooleanField(
        default=False, verbose_name=_("Requiert des photos")
    )
    photo_instructions = models.TextField(
        blank=True, verbose_name=_("Instructions pour les photos")
    )

    expected_duration_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Durée estimée (heures)"),
    )
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0, verbose_name=_("Ordre d'affichage"))

    class Meta:
        verbose_name = _("Type de Tâche")
        verbose_name_plural = _("Types de Tâches")
        ordering = ["category", "order", "name"]

    def __str__(self):
        return f"{self.name} ({self.code})"


class ProjectType(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name=_("Nom du Type"))
    description = models.TextField(blank=True, verbose_name=_("Description"))

    # 💡 Ce champ est la CLÉ pour la logique de l'interface !
    is_transmission = models.BooleanField(
        default=False,
        verbose_name=_(
            "Est un type de projet Transmission (nécessite une liaison A/B)"
        ),
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = _("Type de Projet")
        verbose_name_plural = _("Types de Projets")
        ordering = ["name"]

    def __str__(self):
        return self.name


# =================================================================
# 2. Modèle Project (Le Contrat Client)
# =================================================================


class Project(models.Model):
    country = models.ForeignKey(
        'users.Country',  # Utilise une chaîne pour éviter l'import circulaire
        on_delete=models.PROTECT,
        verbose_name=_("Pays d'Exécution"),
        help_text=_("Le pays détermine l'isolation des données."),
    )
    client = models.ForeignKey(
        Client,  # ✅ OK : Client est défini ci-dessus
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Client")
    )

    name = models.CharField(max_length=200, verbose_name=_("Nom du Projet"))

    budget_alloue = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name=_("Budget Alloué"),
    )

    statut = models.CharField(
        max_length=20,
        choices=PROJECT_STATUS_CHOICES,
        default="PREPARATION",
        verbose_name=_("Statut"),
    )

    coordinator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="coordinated_projects",
        verbose_name=_("Coordonnateur du Projet"),
        help_text=_(
            "L'utilisateur désigné pour gérer le projet (Project Coordinator/CM)."
        ),
    )

    start_date = models.DateField(verbose_name=_("Date de Démarrage"))
    end_date = models.DateField(
        blank=True, null=True, verbose_name=_("Date de Fin Estimée")
    )

    is_active = models.BooleanField(default=True, verbose_name=_("Projet Actif"))
    is_completed = models.BooleanField(default=False, verbose_name=_("Projet Terminé"))

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="projects_created",
        verbose_name=_("Créé par (Traçabilité)"),
    )

    project_type = models.ForeignKey(
        ProjectType,  # ✅ OK : ProjectType est défini ci-dessus
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="projects",
        verbose_name=_("Type de Projet"),
    )

    progress_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name=_("Progression Globale (%)"),
    )

    class Meta:
        verbose_name = _("Projet")
        verbose_name_plural = _("Projets")
        unique_together = ("country", "name")

    def __str__(self):
        return f"{self.name} ({self.country.code})"

    def update_progress(self):
        """
        Recalcule la progression globale du projet basée sur les sites.
        """
        progress_data = self.sites.aggregate(avg_progress=Avg("progress_percentage"))
        self.progress_percentage = progress_data["avg_progress"] or Decimal("0.00")

        if self.statut not in ['INVOICED', 'PAID']:
            if self.progress_percentage >= 100:
                self.statut = 'COMPLETED'
            elif self.progress_percentage > 0:
                self.statut = 'IN_PROGRESS'
            else:
                self.statut = 'PREPARATION'
        
        self.save()
        
    def calculate_total_expenses(self):
        """Calcule le total des dépenses pour ce projet."""
        
        # 👇 IMPORTATION LOCALE
        from finance.models import Depense 
        
        # ✅ CORRECTION :
        # On utilise 'projet_associe' qui est la clé étrangère
        # directe vers Project dans ton modèle Depense.
        return self.depenses.aggregate(
            total=models.Sum("montant", default=Decimal("0.00"))
        )["total"]

# =================================================================
# 3. Modèle Site (Le Lieu d'Intervention)
# =================================================================
class Site(models.Model):
    # Infos de base
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="sites",
        verbose_name=_("Projet Parent"),
    )
    site_id_client = models.CharField(
        max_length=50, unique=True, verbose_name=_("ID du Site Client")
    )  # ID du Site*
    name = models.CharField(
        max_length=200, verbose_name=_("Nom du Site")
    )  # Nom du Site*
    location = models.CharField(
        max_length=255, blank=True, verbose_name=_("Localisation")
    )
    site_area = models.CharField(
        max_length=100, blank=True, verbose_name=_("Site Area")
    )  # Site Area

    departement = models.ForeignKey(
        Departement,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name=_("Département"),
    )

    # Ces champs doivent exister pour la logique transmission
    is_transmission_a_site = models.BooleanField(
        default=False, verbose_name=_("Site A de Transmission")
    )
    is_transmission_b_site = models.BooleanField(
        default=False, verbose_name=_("Site B de Transmission")
    )

    # 📌 Team Lead Assigné
    team_lead = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="led_sites",
        verbose_name=_("Team Lead Assigné"),
    )
    
    start_date = models.DateField(
        verbose_name=_("Date de Démarrage"),
        default=date.today
    )
    end_date = models.DateField(
        verbose_name=_("Date de Fin"), 
        null=True, 
        blank=True
    )

    # 📌 Clés Étrangères vers les NOUVELLES Références (Lookup Models)
    phase = models.ForeignKey(
        SitePhase,  # ✅ OK
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name=_("Phase"),
    )  # Phase
    batch = models.ForeignKey(
        Batch,  # ✅ OK
        on_delete=models.PROTECT, 
        null=True, 
        blank=True, 
        verbose_name=_("Batch")
    )  # Batch
    project_scope = models.TextField(
        blank=True, verbose_name=_("Portée du Projet")
    )  # Portée du projet
    antenna_type = models.ForeignKey(
        AntennaType,  # ✅ OK
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name=_("Type d'Antenne"),
    )  # Type d'antenne
    enclosure_type = models.ForeignKey(
        EnclosureType,  # ✅ OK
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name=_("Type d'Enclosure"),
    )  # Type d'ENCLOSURE
    bb_ml = models.ForeignKey(
        BBMLType,  # ✅ OK
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name=_("BB / ML"),
    )  # BB / ML

    # NOUVEAU Champ COMMENTAIRE
    comment = models.TextField(
        blank=True, verbose_name=_("Commentaire du Site")
    )  # COMMENT

    prix_facturation = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name=_("Prix de Facturation")
    )
    po_recu = models.BooleanField(default=False, verbose_name=_("PO Reçu"))

    status = models.CharField(
        max_length=20, default="TO_DO", verbose_name=_("Statut Général du Site")
    )

    progress_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name=_("Progression (%)"),
    )

    # NOUVEAUX CHAMPS DE CONFIGURATION
    site_type = models.ForeignKey(
        SiteType,  # ✅ OK
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sites",
        verbose_name=_("Type de Site"),
    )
    installation_type = models.ForeignKey(
        InstallationType,  # ✅ OK
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sites",
        verbose_name=_("Type d'Installation"),
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="sites_created",
        verbose_name=_("Créé par (Traçabilité)"),
    )

    last_inspection_result = models.CharField(
        max_length=5,
        blank=True,
        null=True,
        choices=INSPECTION_RESULT_CHOICES,
        verbose_name=_("Résultat Dernière Inspection"),
    )

    class Meta:
        verbose_name = _("Site")
        verbose_name_plural = _("Sites")
        ordering = ["project", "site_id_client"]

    def __str__(self):
        return f"{self.site_id_client} - {self.name}"

    def _get_task_status(self, task_type_code):
        """Fonction utilitaire pour vérifier si une tâche de type donné est COMPLETED."""
        task = (
            self.tasks.filter(task_type__code=task_type_code)
            .order_by("-due_date")
            .first()
        )
        if task and task.status == "COMPLETED":
            return _("Complété")
        elif task:
            return _("En Cours")
        return _("À Faire")

    @property
    def installation_status(self):
        return self._get_task_status("INSTALLATION")

    @property
    def integration_status(self):
        return self._get_task_status("INTEGRATION")

    @property
    def srs_status(self):
        return self._get_task_status("SRS")

    @property
    def imk_status(self):
        return self._get_task_status("IMK")

    @property
    def atp_status(self):
        return self._get_task_status("ATP")

    @property
    def ehs_status(self):
        return self._get_task_status("EHS")

    @property
    def qa_result(self):
        last_qa = (
            self.inspections.filter(type_inspection="ATP")
            .order_by("-date_inspection")
            .first()
        )
        if last_qa:
            return last_qa.get_resultat_inspection_display()
        return _("N/A")

    def update_progress(self):
        """
        Recalcule la progression du site basée sur les tâches et cascade au projet.
        """
        progress_data = self.tasks.aggregate(avg_progress=Avg("progress_percentage"))

        new_progress = progress_data["avg_progress"] or Decimal("0.00")
        self.progress_percentage = new_progress

        if new_progress >= 100:
            self.status = 'COMPLETED'
        elif new_progress > 0:
            self.status = 'IN_PROGRESS'
        else:
            self.status = 'TO_DO'

        self.save()

        # Cascade vers le projet parent
        self.project.update_progress()


# =================================================================
# 4. Modèle SiteRadioConfiguration (Jonction M2M avec data)
# =================================================================
class SiteRadioConfiguration(models.Model):
    site = models.ForeignKey(
        Site,
        on_delete=models.CASCADE,
        related_name="radio_configurations",
        verbose_name=_("Site"),
    )
    radio_type = models.ForeignKey(
        RadioType,  # ✅ OK
        on_delete=models.PROTECT, 
        verbose_name=_("Modèle de Radio")
    )
    quantity = models.IntegerField(
        default=1, validators=[MinValueValidator(1)], verbose_name=_("Quantité")
    )

    class Meta:
        verbose_name = _("Configuration Radio")
        verbose_name_plural = _("Configurations Radio")
        unique_together = (
            "site",
            "radio_type",
        )

    def __str__(self):
        return f"{self.quantity}x {self.radio_type.name} sur {self.site.site_id_client}"


# =================================================================
# 5. Modèle Task (Tâche à réaliser)
# =================================================================
class Task(models.Model):
    site = models.ForeignKey(
        Site,
        on_delete=models.CASCADE,
        related_name="tasks",
        verbose_name=_("Site Associé"),
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="tasks_created",
        verbose_name=_("Créé par"),
    )

    result_type = models.ForeignKey(
        TaskResultType,  # ✅ OK
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Résultat de la tâche"),
    )

    completion_date = models.DateTimeField(
        null=True, blank=True, verbose_name=_("Date de complétion")
    )

    task_type = models.ForeignKey(
        TaskType,  # ✅ OK
        on_delete=models.PROTECT,
        verbose_name=_("Type de tâche"),
    )

    description = models.TextField(verbose_name=_("Description de la Tâche"))

    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="assigned_tasks",
        verbose_name=_("Assigné à"),
    )
    due_date = models.DateField(verbose_name=_("Date Limite"))

    status = models.CharField(
        max_length=20,
        choices=TASK_STATUS_CHOICES,
        default="TO_DO",
        verbose_name=_("Statut"),
    )
    progress_percentage = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name=_("Progression (%)"),
    )

    ticket_number = models.CharField(
        max_length=100, 
        blank=True, 
        null=True, 
        verbose_name=_("Numéro de Ticket")
    )

    expected_duration_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Durée Estimée (h)"),
    )
    is_paid_relevant = models.BooleanField(
        default=False, verbose_name=_("Pertinent pour la Paie")
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Tâche")
        verbose_name_plural = _("Tâches")
        ordering = ["due_date", "site__site_id_client"]

    def __str__(self):
        return f"[{self.site.site_id_client}] {self.description[:30]}..."

    def save(self, *args, **kwargs):
        if self.status == 'TO_DO':
            self.progress_percentage = 0
        elif self.status == 'IN_PROGRESS':
            self.progress_percentage = 50
        elif self.status == 'QC_PENDING':
            self.progress_percentage = 75
        elif self.status == 'COMPLETED':
            self.progress_percentage = 100
        super(Task, self).save(*args, **kwargs)


# =================================================================
# 6. Modèle WorkCompletionRecord (AJOUTÉ CAR MANQUANT)
# =================================================================
class WorkCompletionRecord(models.Model):
    """
    Enregistrement des travaux effectués par un employé sur une tâche.
    Utilisé pour la paie et le suivi de la progression.
    """
    task = models.ForeignKey(
        Task, 
        on_delete=models.CASCADE, 
        related_name="work_records",
        verbose_name=_("Tâche")
    )
    # Dans vos signaux, vous l'appelez 'employee', pas 'user'
    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="work_records",
        verbose_name=_("Employé")
    )
    date = models.DateField(default=date.today, verbose_name=_("Date du travail"))
    
    duration_hours = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=Decimal("0.00"),
        verbose_name=_("Durée (heures)")
    )
    completion_percentage = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name=_("Achèvement (%)")
    )
    
    # Champs pour la paie (calculés par le signal)
    hourly_rate_used = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        verbose_name=_("Taux Horaire Utilisé")
    )
    cost = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        verbose_name=_("Coût (Paie)")
    )
    is_paid_out = models.BooleanField(default=False, verbose_name=_("Est Payé"))

    # Traçabilité
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_work_records",
        verbose_name=_("Saisi par")
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Enregistrement de Travail")
        verbose_name_plural = _("Enregistrements de Travail")
        ordering = ['-date']

    def __str__(self):
        return f"Travail sur {self.task} par {self.employee.username} le {self.date}"


# =================================================================
# 7. Modèle TaskPhoto (DÉPEND DE TASK)
# =================================================================
class TaskPhoto(models.Model):
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name="task_images",
    )

    photo = models.ImageField(
        upload_to="task_photos/%Y/%m/%d/", verbose_name=_("Photo")
    )
    caption = models.CharField(max_length=255, blank=True, verbose_name=_("Légende"))
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Photo de Tâche")
        verbose_name_plural = _("Photos de Tâches")
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"Photo pour {self.task} - {self.uploaded_at}"


# =================================================================
# 8. Modèle Inspection (DÉPEND DE SITE)
# =================================================================
class Inspection(models.Model):
    site = models.ForeignKey(
        Site,
        on_delete=models.CASCADE,
        related_name="inspections",
        verbose_name=_("Site Inspecté"),
    )
    type_inspection = models.CharField(
        max_length=10,
        choices=INSPECTION_TYPE_CHOICES,
        verbose_name=_("Type d'Inspection"),
    )
    inspector = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="inspections_performed",
        verbose_name=_("Inspecteur"),
    )
    resultat_inspection = models.CharField(
        max_length=5,
        choices=INSPECTION_RESULT_CHOICES,
        verbose_name=_("Résultat"),
    )
    date_inspection = models.DateField(
        default=date.today, verbose_name=_("Date de l'Inspection")
    )
    rapport_photos_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name=_("Lien Rapport Photos/Drive"),
    )
    commentaires = models.TextField(
        blank=True, verbose_name=_("Commentaires de l'Inspecteur")
    )

    class Meta:
        verbose_name = _("Inspection")
        verbose_name_plural = _("Inspections")
        ordering = ["-date_inspection"]

    def __str__(self):
        return f"Inspection {self.type_inspection} - {self.site.site_id_client}"


# =================================================================
# 9. Modèle TransmissionLink (DÉPEND DE SITE)
# =================================================================
class TransmissionLink(models.Model):
    """
    Modèle pour lier deux sites ensemble dans le cadre d'une installation Transmission.
    """
    link_id = models.CharField(
        max_length=50, unique=True, verbose_name=_("ID de la Liaison")
    )

    site_a = models.OneToOneField(
        Site,
        on_delete=models.CASCADE,
        related_name="transmission_link_a",
        verbose_name=_("Site A"),
    )
    site_b = models.OneToOneField(
        Site,
        on_delete=models.CASCADE,
        related_name="transmission_link_b",
        verbose_name=_("Site B"),
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Liaison Transmission")
        verbose_name_plural = _("Liaisons Transmission")

    def __str__(self):
        return f"Liaison {self.link_id}: {self.site_a.site_id_client} <-> {self.site_b.site_id_client}"