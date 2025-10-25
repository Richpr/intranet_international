from django.contrib import admin
from .models import SalaryStructure, DailyExpense, WorkCompletionRecord


# =================================================================
# 1. Admin SalaryStructure (AVEC ISOLATION)
# =================================================================
@admin.register(SalaryStructure)
class SalaryStructureAdmin(admin.ModelAdmin):
    list_display = ("country", "role", "base_amount")
    list_filter = ("country", "role")
    search_fields = ("country__name", "role__name")
    raw_id_fields = ("country", "role")

    # Logique d'isolation
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs

        active_country_ids = request.user.active_countries
        return qs.filter(country__id__in=active_country_ids)

    # Assure que le Country Manager peut gérer les coûts de son pays
    def has_change_permission(self, request, obj=None):
        perm = super().has_change_permission(request, obj)
        if request.user.is_superuser:
            return perm

        # Le CEO et le Country Manager/RAF du pays peuvent gérer la structure
        if (
            request.user.has_role("CEO")
            or request.user.has_role("Country Manager")
            or request.user.has_role("RAF")
        ):
            if obj and obj.country_id in request.user.active_countries:
                return perm

        return (
            perm and obj is None
        )  # Permet seulement l'ajout si pas d'objet spécifique


# =================================================================
# 2. Admin DailyExpense (AVEC ISOLATION)
# =================================================================
@admin.register(DailyExpense)
class DailyExpenseAdmin(admin.ModelAdmin):
    list_display = ("date", "country", "site", "amount", "is_approved")
    list_filter = ("country", "is_approved")
    search_fields = ("description", "site__site_id_client")
    raw_id_fields = ("country", "site", "created_by")

    # Logique d'isolation
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs

        active_country_ids = request.user.active_countries
        return qs.filter(country__id__in=active_country_ids)

    # Logique de traçabilité (remplir 'created_by')
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


# =================================================================
# 3. Admin WorkCompletionRecord (Paie Terrain) (AVEC ISOLATION)
# =================================================================


@admin.register(WorkCompletionRecord)
class WorkCompletionRecordAdmin(admin.ModelAdmin):
    # Les champs 'user' et 'task' sont des ForeignKeys, elles peuvent être des raw_id_fields.
    # Nous utilisons 'user' car c'est le nom de notre champ.
    raw_id_fields = ["employee", "task", "created_by"]

    # Les colonnes affichées dans la liste
    list_display = (
        "date",
        "employee",  # Champ réel de l'employé
        "task",
        "duration_hours",
        "completion_percentage",
        "created_at",
    )

    # Filtres de la liste
    list_filter = (
        "date",
        "task",
        # 'user' fonctionne comme filtre, pas besoin de le renommer
    )

    # Champs pour le formulaire d'édition
    fields = (
        ("employee", "date"),
        ("task", "duration_hours", "completion_percentage"),
        "created_by",
        "created_at",
    )

    # Retirer tous les list_editable, car nous n'avons pas de champ simple pour l'édition rapide.
    # Si vous avez cette ligne, retirez-la :
    # list_editable = ('is_paid_out',) # <--- À RETIRER

    # Retirer les champs qui n'existent pas du search_fields, s'ils y sont.
    search_fields = (
        "employee__username",  # Recherche par nom d'utilisateur
        "task__name",
    )

    readonly_fields = ("created_at",)
