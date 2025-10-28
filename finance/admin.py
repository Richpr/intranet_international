from django.contrib import admin
from .models import Depense, Revenu


@admin.register(Depense)
class DepenseAdmin(admin.ModelAdmin):
    list_display = ('date', 'montant', 'categorie', 'projet_associe', 'employe_declarant')
    list_filter = ('categorie', 'projet_associe', 'employe_declarant')
    search_fields = ('description',)


@admin.register(Revenu)
class RevenuAdmin(admin.ModelAdmin):
    list_display = ('date', 'montant', 'projet_facture')
    list_filter = ('projet_facture',)
