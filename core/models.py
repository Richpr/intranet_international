from django.db import models
from django.utils.translation import gettext_lazy as _
from users.models import Country

class Departement(models.Model):
    name = models.CharField(max_length=100, verbose_name=_("Nom du Département"))
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name="departements", verbose_name=_("Pays"))
    is_active = models.BooleanField(default=True, verbose_name=_("Actif"))

    class Meta:
        verbose_name = _("Département")
        verbose_name_plural = _("Départements")
        unique_together = ('name', 'country')
        ordering = ['country', 'name']

    def __str__(self):
        return f"{self.name} ({self.country.code})"