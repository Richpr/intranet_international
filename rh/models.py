from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from finance.models import Depense
from datetime import date

# Create your models here.

class Certification(models.Model):
    employe = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="certifications", verbose_name=_("Employé"))
    nom_certification = models.CharField(max_length=200, verbose_name=_("Nom de la certification"))
    date_expiration = models.DateField(verbose_name=_("Date d'expiration"))
    depense_associee = models.ForeignKey(Depense, on_delete=models.SET_NULL, null=True, blank=True, related_name="certifications", verbose_name=_("Dépense associée"))
    fichier_certificat = models.FileField(upload_to='certifications/', verbose_name=_("Fichier du certificat"))

    @property
    def statut_expiration(self):
        today = date.today()
        if self.date_expiration < today:
            return "Expiré"
        elif (self.date_expiration - today).days <= 30:
            return "Expire bientôt"
        else:
            return "Valide"

    class Meta:
        verbose_name = _("Certification")
        verbose_name_plural = _("Certifications")

    def __str__(self):
        return f"{self.nom_certification} pour {self.employe}"

class PaiementSalaire(models.Model):
    employe = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="paiements_salaires", verbose_name=_("Employé"))
    mois = models.IntegerField(verbose_name=_("Mois"))
    annee = models.IntegerField(verbose_name=_("Année"))
    montant_paye = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Montant payé"))
    depense_associee = models.OneToOneField(Depense, on_delete=models.CASCADE, related_name="paiement_salaire", verbose_name=_("Dépense associée"))

    class Meta:
        verbose_name = _("Paiement de Salaire")
        verbose_name_plural = _("Paiements de Salaires")
        unique_together = ("employe", "mois", "annee")

    def __str__(self):
        return f"Salaire de {self.employe} pour {self.mois}/{self.annee}"


class Contract(models.Model):
    employee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='contracts')
    job_title = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_signed = models.BooleanField(default=False)
    file = models.FileField(upload_to='contracts/', null=True, blank=True)

    def __str__(self):
        return f"Contract for {self.employee.username} - {self.job_title}"

class DocumentCounter(models.Model):
    document_type = models.CharField(max_length=50, verbose_name=_("Type de document"))
    year = models.IntegerField(verbose_name=_("Année"))
    last_number = models.IntegerField(default=0, verbose_name=_("Dernier numéro utilisé"))

    class Meta:
        verbose_name = _("Compteur de document")
        verbose_name_plural = _("Compteurs de documents")
        unique_together = ('document_type', 'year')

    def __str__(self):
        return f"Compteur pour {self.document_type} ({self.year}): {self.last_number}"