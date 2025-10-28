from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from projects.models import Site

# Create your models here.

class Vehicule(models.Model):
    TYPE_CHOICES = (
        ("PROPRIETAIRE", _("Propriétaire")),
        ("LOUE", _("Loué")),
    )
    STATUT_CHOICES = (
        ("OPERATIONNEL", _("Opérationnel")),
        ("EN_REPARATION", _("En réparation")),
        ("HORS_SERVICE", _("Hors service")),
    )

    nom_vehicule = models.CharField(max_length=200, verbose_name=_("Nom du véhicule"))
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, verbose_name=_("Type"))
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="OPERATIONNEL", verbose_name=_("Statut"))

    class Meta:
        verbose_name = _("Véhicule")
        verbose_name_plural = _("Véhicules")

    def __str__(self):
        return self.nom_vehicule

class MissionLogistique(models.Model):
    vehicule = models.ForeignKey(Vehicule, on_delete=models.CASCADE, related_name="missions", verbose_name=_("Véhicule"))
    conducteur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="missions_conduites", verbose_name=_("Conducteur"))
    motif = models.CharField(max_length=255, verbose_name=_("Motif"))
    site_concerne = models.ForeignKey(Site, on_delete=models.CASCADE, related_name="missions_logistiques", verbose_name=_("Site concerné"))

    class Meta:
        verbose_name = _("Mission Logistique")
        verbose_name_plural = _("Missions Logistiques")

    def __str__(self):
        return f"Mission du {self.conducteur} avec {self.vehicule} pour {self.site_concerne}"
