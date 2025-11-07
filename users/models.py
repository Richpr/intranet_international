from django.db import models
from django.contrib.auth.models import AbstractUser
from datetime import date
from django.utils.translation import gettext_lazy as _
from projects.models import Project, Task
from decimal import Decimal
from django.db.models import F

# =================================================================
# 1. Modèle Country (Le Locataire / Tenant)
# =================================================================
class Country(models.Model):
    name = models.CharField(
        max_length=100, unique=True, verbose_name=_("Nom du Pays/Filiale")
    )
    code = models.CharField(
        max_length=5, unique=True, verbose_name=_("Code (Ex: BEN, TGO)")
    )
    is_active = models.BooleanField(default=True, verbose_name=_("Filiale Active"))

    class Meta:
        verbose_name = _("Pays/Filiale")
        verbose_name_plural = _("Pays/Filiales")

    def __str__(self):
        return self.name


# =================================================================
# 2. Modèle Role (Le Titre/Rôle de l'employé)
# =================================================================
class Role(models.Model):
    name = models.CharField(
        max_length=100, unique=True, verbose_name=_("Titre du Rôle")
    )

    class Meta:
        verbose_name = _("Rôle")
        verbose_name_plural = _("Rôles")

    def __str__(self):
        return self.name

# =================================================================
# 3. Modèle CustomUser (L'Employé)
# =================================================================

EMPLOYEE_STATUS_CHOICES = (
    ("ACTIF", _("Actif")),
    ("EN_CONGE", _("En congé")),
    ("INACTIF", _("Inactif")),
)

class CustomUser(AbstractUser):
    phone_number = models.CharField(
        max_length=20, blank=True, null=True, verbose_name="Numéro de téléphone"
    )
    salaire_mensuel_base = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00"), verbose_name=_("Salaire Mensuel de Base")
    )
    statut_actuel = models.CharField(
        max_length=20,
        choices=EMPLOYEE_STATUS_CHOICES,
        default="ACTIF",
        verbose_name=_("Statut actuel"),
    )
    manager = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='team_members', verbose_name=_("Manager"))

    class Meta:
        verbose_name = "Employé"
        verbose_name_plural = "Employés"

    # Méthodes de vérification de rôle (version méthode)
    def is_team_lead_user(self):
        """Vérifie si l'utilisateur appartient au groupe 'Team_Lead'."""
        return self.groups.filter(name__iexact="Team_Lead").exists()

    def is_coordinator_user(self):
        """Vérifie si l'utilisateur est un Project Coordinator actif."""
        user_roles = {r.lower() for r in self.get_active_role_names()}
        return (
            "coordinateur de projet" in user_roles or "coordinateur_de_projet" in user_roles
        )

    def is_field_team_user(self):
        """Vérifie si l'utilisateur fait partie de la Field Team active."""
        user_roles = {r.lower() for r in self.get_active_role_names()}
        return "field team" in user_roles or "field_team" in user_roles

    # Propriétés pour un accès plus simple (version propriété)
    @property
    def is_cm(self):
        """Propriété pour user.is_cm (utilisée dans les vues)"""
        user_roles = {r.lower() for r in self.get_active_role_names()}
        return "country manager" in user_roles or "country_manager" in user_roles

    @property
    def is_coordinator(self):
        """Propriété pour user.is_coordinator (utilisée dans les vues)"""
        return self.is_coordinator_user()

    @property
    def is_field_team(self):
        """Propriété pour user.is_field_team (utilisée dans les vues)"""
        return self.is_field_team_user()

    @property
    def is_team_lead(self):
        """Propriété pour user.is_team_lead (utilisée dans les vues)"""
        return self.is_team_lead_user()

    # Propriété pour obtenir la liste des IDs de pays où l'utilisateur est ACTIVE
    @property
    def active_country_ids(self):
        """
        Retourne la liste des IDs des pays pour lesquels l'utilisateur a une affectation active.
        C'est le filtre de base pour l'isolation des données (Country Isolation).
        """
        if not self.is_authenticated:
            return []

        return list(
            self.assignments.filter(is_active=True, country__is_active=True)
            .values_list("country_id", flat=True)
            .distinct()
        )

    @property
    def active_countries_objects(self):
        """
        Retourne les objets Country actifs de l'utilisateur.
        """
        # Import local pour éviter la dépendance circulaire si Country est dans le même fichier
        from .models import Country

        # Correction : utiliser active_country_ids au lieu de active_countries_objects
        active_ids = self.active_country_ids

        return Country.objects.filter(id__in=active_ids, is_active=True).order_by(
            "name"
        )

    @property
    def main_role(self):
        """
        Détermine le rôle principal de l'utilisateur selon une hiérarchie.
        """
        user_roles = {r.lower() for r in self.get_active_role_names()}

        # Définition de la hiérarchie
        if self.is_superuser:
            return "Administrateur Système"
        if "country manager" in user_roles or "country_manager" in user_roles:
            return "Country Manager"
        if ("project coordinator" in user_roles or "project_coordinator" in user_roles) or self.coordinated_projects.filter(is_active=True).exists():
            return "Coordinateur de Projet"
        if self.is_team_lead_user():
            return "Team Lead"
        if "field team" in user_roles or "field_team" in user_roles:
            return "Field Team"
        else:
            return "Employé"

    def get_active_role_names(self):
        """
        Retourne un ensemble (set) de tous les noms de rôles actifs de l'utilisateur.
        """
        if not self.is_authenticated:
            return set()

        return set(
            self.assignments.filter(
                is_active=True, country__is_active=True
            ).values_list("role__name", flat=True)
        )

    # Méthode pour vérifier si l'utilisateur possède un rôle dans l'un de ses pays actifs
    def has_role(self, role_name):
        return self.assignments.filter(
            role__name=role_name,
            country_id__in=self.active_country_ids,  # Correction : utiliser active_country_ids
            is_active=True,
        ).exists()

    def technician_completion_rate(self):
        """Taux d'achèvement pour un technicien."""
        assigned_tasks = self.assigned_tasks.all()
        if not assigned_tasks.exists():
            return Decimal('0.00')
        
        completed_tasks = assigned_tasks.filter(status='COMPLETED', result_type__is_success=True).count()
        total_tasks = assigned_tasks.count()
        
        return (Decimal(completed_tasks) / Decimal(total_tasks)) * 100 if total_tasks > 0 else Decimal('0.00')

    def team_lead_success_rate(self):
        """Taux de succès pour un Team Lead."""
        led_sites = self.led_sites.all()
        if not led_sites.exists():
            return Decimal('0.00')
            
        tasks = Task.objects.filter(site__in=led_sites)
        if not tasks.exists():
            return Decimal('0.00')
            
        successful_tasks = tasks.filter(status='COMPLETED', result_type__is_success=True).count()
        total_tasks = tasks.count()
        
        return (Decimal(successful_tasks) / Decimal(total_tasks)) * 100 if total_tasks > 0 else Decimal('0.00')

    def coordinator_on_time_completion_rate(self):
        """Taux de complétion à temps pour un coordinateur."""
        coordinated_projects = self.coordinated_projects.all()
        if not coordinated_projects.exists():
            return Decimal('0.00')
            
        tasks = Task.objects.filter(site__project__in=coordinated_projects)
        if not tasks.exists():
            return Decimal('0.00')
            
        on_time_tasks = tasks.filter(completion_date__isnull=False, completion_date__date__lte=models.F('due_date')).count()
        total_tasks = tasks.count()
        
        return (Decimal(on_time_tasks) / Decimal(total_tasks)) * 100 if total_tasks > 0 else Decimal('0.00')


# =================================================================
# 4. Modèle Assignation (Lien Employé-Projet)
# =================================================================
class Assignation(models.Model):
    employe = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="assignations_projet", verbose_name=_("Employé"))
    projet = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="assignations_employe", verbose_name=_("Projet"))
    date_debut_assignation = models.DateField(verbose_name=_("Date de début d'assignation"))
    date_fin_assignation = models.DateField(blank=True, null=True, verbose_name=_("Date de fin d'assignation"))

    class Meta:
        verbose_name = _("Assignation Projet")
        verbose_name_plural = _("Assignations Projet")
        unique_together = ("employe", "projet", "date_debut_assignation")

    def __str__(self):
        return f"{self.employe.username} assigné à {self.projet.name}"


# =================================================================
# 5. Modèle EmployeeCountryAssignment (L'Affectation Dynamique)
# =================================================================
class EmployeeCountryAssignment(models.Model):
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="assignments",
        verbose_name=_("Employé"),
    )
    country = models.ForeignKey(
        Country, on_delete=models.PROTECT, verbose_name=_("Pays/Filiale")
    )
    role = models.ForeignKey(
        Role, on_delete=models.PROTECT, verbose_name=_("Rôle dans ce Pays")
    )

    start_date = models.DateField(
        default=date.today, verbose_name=_("Date de début de l'affectation")
    )

    end_date = models.DateField(
        blank=True,
        null=True,
        verbose_name=_("Date de fin (Laisser vide pour permanent)"),
    )
    is_active = models.BooleanField(
        default=True, help_text=_("Permet de désactiver manuellement une affectation.")
    )

    class Meta:
        verbose_name = _("Affectation Pays/Rôle")
        verbose_name_plural = _("Affectations Pays/Rôles")
        unique_together = ("user", "country", "role", "start_date")

    def __str__(self):
        return f"{self.user.username} - {self.role.name} ({self.country.code})"
