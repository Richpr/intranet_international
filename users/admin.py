from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Country, Role, EmployeeCountryAssignment


# =================================================================
# 1. Configuration de l'Inline pour les Affectations (pour le profil utilisateur)
# =================================================================
class EmployeeCountryAssignmentInline(admin.TabularInline):
    # Permet d'éditer les affectations directement dans le formulaire de l'utilisateur
    model = EmployeeCountryAssignment
    extra = 1  # Affiche 1 formulaire d'affectation vide par défaut

    # Utiliser un sélecteur de recherche pour les clés étrangères (plus pratique)
    raw_id_fields = ("country", "role")


# =================================================================
# 2. Configuration de l'Administration CustomUser
# =================================================================
class CustomUserAdmin(UserAdmin):
    # Ajout du champ phone_number à la liste d'affichage
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "phone_number",
        "is_staff",
    )

    # Ajout du champ phone_number au formulaire
    fieldsets = UserAdmin.fieldsets + (
        ("Informations Personnelles", {"fields": ("phone_number",)}),
    )

    # Intégration de l'éditeur d'affectation (Inline)
    inlines = [
        EmployeeCountryAssignmentInline,
    ]


# =================================================================
# 3. Enregistrement des Modèles de Base
# =================================================================
@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):

    list_display = ("name", "code", "is_active")
    list_editable = ("is_active",)
    search_fields = ("name", "code")  # Ajouté/Confirmé : Active la recherche


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


# Enregistrement du CustomUser
admin.site.register(CustomUser, CustomUserAdmin)
