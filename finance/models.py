from django.db import models
from decimal import Decimal
from django.utils.translation import gettext_lazy as _
from users.models import Country, Role, CustomUser
from projects.models import Project, Site
from logistique.models import Vehicule
from inventaire.models import Equipement
from django.conf import settings
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
import sys


# =================================================================
# CHOIX POUR LES MODÈLES
# =================================================================

DEPENSE_CATEGORIE_CHOICES = (
    ("LOYER", _("Loyer")),
    ("ELECTRICITE", _("Electricité")),
    ("EAU", _("Eau")),
    ("CARBURANT", _("Carburant")),
    ("SALAIRE", _("Salaire")),
    ("IMPOTS", _("Impôts")),
    ("ACHAT_MATERIEL", _("Achat Matériel")),
    ("REPARATION_VEHICULE", _("Réparation Véhicule")),
    ("REPARATION_EQUIPEMENT", _("Réparation Équipement")),
    ("CERTIFICATION", _("Certification")),
    ("TRANSPORT", _("Transport")),
    ("SOUS_TRAITANT", _("Sous-traitant")),
    ("AUTRE", _("Autre")),
)

# =================================================================
# 1. Modèle Depense
# =================================================================



class SalaryStructure(models.Model):
    country = models.ForeignKey(
        Country, 
        on_delete=models.PROTECT, 
        verbose_name=_("Pays/Filiale")
    )
    role = models.ForeignKey(
        Role, 
        on_delete=models.PROTECT, 
        verbose_name=_("Rôle")
    )
    base_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=Decimal("0.00"), 
        verbose_name=_("Montant de base (mensuel)")
    )
    # Ajoutez d'autres champs si nécessaire (devise, etc.)

    class Meta:
        verbose_name = _("Structure Salariale")
        verbose_name_plural = _("Structures Salariales")
        # Assure qu'il n'y a qu'une seule structure par combinaison Pays/Rôle
        unique_together = ("country", "role") 

    def __str__(self):
        return f"Salaire pour {self.role.name} en {self.country.code}: {self.base_amount}"

class Depense(models.Model):
    date = models.DateField(verbose_name=_("Date de la dépense"))
    montant = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Montant"))
    description = models.TextField(verbose_name=_("Description"))
    categorie = models.CharField(max_length=50, choices=DEPENSE_CATEGORIE_CHOICES, verbose_name=_("Catégorie"))
    projet_associe = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True, related_name="depenses", verbose_name=_("Projet associé"))
    site_concerne = models.ForeignKey(Site, on_delete=models.SET_NULL, null=True, blank=True, related_name="depenses", verbose_name=_("Site concerné"))
    vehicule_concerne = models.ForeignKey(Vehicule, on_delete=models.SET_NULL, null=True, blank=True, related_name="depenses", verbose_name=_("Véhicule concerné"))
    equipement_concerne = models.ForeignKey(Equipement, on_delete=models.SET_NULL, null=True, blank=True, related_name="depenses", verbose_name=_("Équipement concerné"))
    employe_declarant = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name="depenses_declarees", verbose_name=_("Employé déclarant"))
    recu_scan = models.FileField(upload_to="recus_depenses/", verbose_name=_("Reçu scanné"))

    class Meta:
        verbose_name = _("Dépense")
        verbose_name_plural = _("Dépenses")
        ordering = ["-date"]

    def __str__(self):
        return f"Dépense du {self.date} - {self.montant}"

    def save(self, *args, **kwargs):
        if self.recu_scan:
            img = Image.open(self.recu_scan)

            MAX_SIZE = (1280, 1280)
            QUALITY = 85

            if img.size[0] > MAX_SIZE[0] or img.size[1] > MAX_SIZE[1]:
                img.thumbnail(MAX_SIZE, Image.Resampling.LANCZOS)

            output = BytesIO()
            if img.mode == 'RGBA':
                img = img.convert('RGB')

            img.save(output, format='JPEG', quality=QUALITY, optimize=True)
            output.seek(0)

            self.recu_scan = InMemoryUploadedFile(
                output, 
                'ImageField', 
                f"{self.recu_scan.name.split('.')[0]}.jpg", 
                'image/jpeg', 
                sys.getsizeof(output), 
                None
            )

        super().save(*args, **kwargs)

# =================================================================
# 2. Modèle Revenu
# =================================================================
class Revenu(models.Model):
    date = models.DateField(verbose_name=_("Date de réception du paiement"))
    montant = models.DecimalField(max_digits=12, decimal_places=2, verbose_name=_("Montant reçu"))
    projet_facture = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="revenus", verbose_name=_("Projet facturé"))

    class Meta:
        verbose_name = _("Revenu")
        verbose_name_plural = _("Revenus")
        ordering = ["-date"]

    def __str__(self):
        return f"Revenu du {self.date} - {self.montant}"


# =================================================================
# 3. Modèle ObligationFiscale
# =================================================================
class ObligationFiscale(models.Model):
    STATUT_CHOICES = (
        ("A_PAYER", _("À Payer")),
        ("PAYE", _("Payé")),
        ("EN_RETARD", _("En Retard")),
    )

    type_impot = models.CharField(max_length=100, verbose_name=_("Type d'impôt"))
    date_echeance = models.DateField(verbose_name=_("Date d'échéance"))
    montant_a_payer = models.DecimalField(max_digits=12, decimal_places=2, verbose_name=_("Montant à payer"))
    montant_paye = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name=_("Montant payé"))
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="A_PAYER", verbose_name=_("Statut"))
    depense_associee = models.OneToOneField(Depense, on_delete=models.SET_NULL, null=True, blank=True, related_name="obligation_fiscale", verbose_name=_("Dépense associée"))

    class Meta:
        verbose_name = _("Obligation Fiscale")
        verbose_name_plural = _("Obligations Fiscales")
        ordering = ["date_echeance"]

    def __str__(self):
        return f"{self.type_impot} - {self.date_echeance}"
