from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    CustomUser, Country, Role, EmployeeCountryAssignment, Assignation,
    Department, ContractType, IDType, Bank, EmployeeDocument, ProfileUpdate
)

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

class EmployeeDocumentInline(admin.TabularInline):
    model = EmployeeDocument
    extra = 1

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
        ("Informations Personnelles", {
            "fields": (
                "phone_number", "department", "contract_type", "hire_date", "job_role",
                "nationality", "assigned_countries", "other_first_name", "birth_date",
                "birth_country", "blood_group", "address", "id_type", "id_number",
                "professional_email", "allergies", "recurring_illness", "special_allergies",
                "isignum_number", "eritop_id", "bank", "bank_account_number",
                "social_security_number", "profile_picture", "salaire_mensuel_base",
                "statut_actuel", "manager", "employee_id"
            )
        }),
    )

    inlines = [
        EmployeeCountryAssignmentInline,
        AssignationInline,
        EmployeeDocumentInline,
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

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(ContractType)
class ContractTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(IDType)
class IDTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Bank)
class BankAdmin(admin.ModelAdmin):
    list_display = ('name', 'country')
    search_fields = ('name', 'country__name')

@admin.register(EmployeeDocument)
class EmployeeDocumentAdmin(admin.ModelAdmin):
    list_display = ('employee', 'document_type', 'upload_date')
    search_fields = ('employee__username', 'document_type')

@admin.register(ProfileUpdate)
class ProfileUpdateAdmin(admin.ModelAdmin):
    list_display = ('employee', 'status', 'created_at', 'reviewed_by', 'reviewed_at')
    list_filter = ('status',)
    search_fields = ('employee__username',)

admin.site.register(CustomUser, CustomUserAdmin)
