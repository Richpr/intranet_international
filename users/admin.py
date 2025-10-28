from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Country, Role, EmployeeCountryAssignment, Assignation


# =================================================================
# 1. Configuration de l'Inline pour les Affectations (pour le profil utilisateur)
# =================================================================
class EmployeeCountryAssignmentInline(admin.TabularInline):
    model = EmployeeCountryAssignment
    extra = 1
    raw_id_fields = ("country", "role")

class AssignationInline(admin.TabularInline):
    model = Assignation
    extra = 1
    raw_id_fields = ("employe", "projet")


# =================================================================
# 2. Configuration de l'Administration CustomUser
# =================================================================
class CustomUserAdmin(UserAdmin):
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "phone_number",
        "is_staff",
        "statut_actuel",
    )

    fieldsets = UserAdmin.fieldsets + (
        ("Informations Personnelles", {"fields": ("phone_number", "salaire_mensuel_base", "statut_actuel")}),
    )

    inlines = [
        EmployeeCountryAssignmentInline,
        AssignationInline
    ]


# =================================================================
# 3. Enregistrement des Modèles de Base
# =================================================================
@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "is_active")
    list_editable = ("is_active",)
    search_fields = ("name", "code")

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)

@admin.register(Assignation)
class AssignationAdmin(admin.ModelAdmin):
    list_display = ("employe", "projet", "date_debut_assignation", "date_fin_assignation")
    list_filter = ("projet", "employe")
    search_fields = ("projet__name", "employe__username")


admin.site.register(CustomUser, CustomUserAdmin)
