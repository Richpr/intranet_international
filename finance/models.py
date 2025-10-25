from django.db import models
from django.utils.translation import gettext_lazy as _
from users.models import Country, Role, CustomUser
from projects.models import Site
from django.conf import settings


# =================================================================
# 1. Modèle SalaryStructure (La Structure de Coûts)
# (Pas de changement)
# =================================================================
class SalaryStructure(models.Model):
    country = models.ForeignKey(
        Country, on_delete=models.PROTECT, verbose_name=_("Pays")
    )
    # ... (le reste du modèle)
    role = models.ForeignKey(
        Role, on_delete=models.PROTECT, verbose_name=_("Rôle concerné")
    )
    base_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Montant de base (par jour/mois)"),
    )

    class Meta:
        verbose_name = _("Structure Salariale")
        verbose_name_plural = _("Structures Salariales")
        unique_together = ("country", "role")

    def __str__(self):
        return f"Structure {self.role.name} - {self.country.code}"


# =================================================================
# 2. Modèle DailyExpense (Dépenses/Notes de Frais Quotidiennes)
# (Pas de changement)
# =================================================================
class DailyExpense(models.Model):
    country = models.ForeignKey(
        Country,
        on_delete=models.PROTECT,
        verbose_name=_("Pays"),
        help_text=_("Clé d'isolation."),
    )
    # ... (le reste du modèle)
    site = models.ForeignKey(
        Site,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Site/Localisation"),
    )

    date = models.DateField(verbose_name=_("Date de la Dépense"))
    description = models.CharField(max_length=255, verbose_name=_("Description"))
    amount = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name=_("Montant (€ / XOF etc.)")
    )

    is_approved = models.BooleanField(default=False, verbose_name=_("Approuvée ?"))

    created_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name="daily_expenses",
        verbose_name=_("Saisie par"),
    )

    class Meta:
        verbose_name = _("Dépense Quotidienne")
        verbose_name_plural = _("Dépenses Quotidiennes")
        ordering = ["-date"]

    def __str__(self):
        return f"Dépense {self.country.code} - {self.date} - {self.amount}"


# =================================================================
# 3. Modèle WorkCompletionRecord (Fiche de Paie du Terrain)
# Version FUSIONNÉE et CORRIGÉE
# =================================================================
class WorkCompletionRecord(models.Model):
    """
    Enregistre les heures/jours travaillés ou l'avancement d'une tâche pour la paie.
    Permet un enregistrement par jour/employé/tâche.
    """

    # Liens
    task = models.ForeignKey(
        "projects.Task",  # Utilisation de la chaîne pour éviter les problèmes d'import circulaire
        on_delete=models.PROTECT,  # CHANGEMENT : Protéger la tâche car elle est liée à une paie.
        verbose_name="Tâche Complétée",
    )
    # Renommé en 'employee' pour la clarté, tout en pointant vers l'utilisateur (CustomUser)
    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,  # CHANGEMENT : Protéger l'employé
        verbose_name="Employé (Ouvrier)",
    )

    # Données de travail
    date = models.DateField(verbose_name="Date de travail")
    duration_hours = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Durée (Heures)",
    )
    completion_percentage = models.IntegerField(
        null=True, blank=True, verbose_name="Achèvement de la Tâche (%)"
    )

    # CHAMPS POUR LE CALCUL DE LA PAIE (Nouveaux Ajouts)

    hourly_rate_used = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Taux Horaire Utilisé (pour historique)",
    )

    # Coût total de cet enregistrement de travail (Paie Brute)
    cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Coût de l'Enregistrement",
    )

    # CHAMP FUSIONNÉ du Modèle 1 pour le suivi du paiement
    is_paid_out = models.BooleanField(
        default=False, verbose_name=_("Paiement effectué ?")
    )

    # Méta
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="work_records_created",
    )

    class Meta:
        verbose_name = "Enregistrement d'Achèvement de Travail"
        verbose_name_plural = "Enregistrements d'Achèvement de Travail"
        # Rétablir la contrainte d'unicité sur la nouvelle structure :
        unique_together = ("task", "date", "employee")
        ordering = ["-date", "task__id"]  # Tri par date la plus récente

    def __str__(self):
        # Utilisation de 'employee' à la place de 'user'
        return f"{self.employee.username} - Tâche #{self.task.id} ({self.date})"
