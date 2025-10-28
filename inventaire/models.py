from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings

# Create your models here.

class Equipement(models.Model):
    STATUT_CHOICES = (
        ("EN_STOCK", _("En stock")),
        ("ALLOUE", _("Alloué")),
        ("EN_MAINTENANCE", _("En maintenance")),
        ("HORS_SERVICE", _("Hors service")),
    )

    nom_equipement = models.CharField(max_length=200, verbose_name=_("Nom de l'équipement"))
    numero_serie = models.CharField(max_length=200, unique=True, verbose_name=_("Numéro de série"))
    cout_achat = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Coût d'achat"))
    date_prochaine_inspection = models.DateField(verbose_name=_("Date de prochaine inspection"))
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="EN_STOCK", verbose_name=_("Statut"))

    class Meta:
        verbose_name = _("Équipement")
        verbose_name_plural = _("Équipements")

    def __str__(self):
        return self.nom_equipement

class AllocationEquipement(models.Model):
    equipement = models.ForeignKey(Equipement, on_delete=models.CASCADE, related_name="allocations", verbose_name=_("Équipement"))
    employe_assigne = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="equipements_assignes", verbose_name=_("Employé assigné"))
    date_assignation = models.DateField(verbose_name=_("Date d'assignation"))

    class Meta:
        verbose_name = _("Allocation d'équipement")
        verbose_name_plural = _("Allocations d'équipement")

    def __str__(self):
        return f"{self.equipement} alloué à {self.employe_assigne} le {self.date_assignation}"
