from django.contrib import admin
from .models import (
    TaskType,
    Project,
    Site,
    Task,
    Inspection,
    SitePhase,
    Batch,
    AntennaType,
    EnclosureType,
    BBMLType,
    RadioType,
    SiteRadioConfiguration,
    SiteType,
    InstallationType,
    TransmissionLink,
    ProjectType,
    Client,
)


# =================================================================
# Inline 1 : Task (Niveau le plus bas, utilisé par Site)
# =================================================================
class TaskInline(admin.TabularInline):
    model = Task
    extra = 1
    raw_id_fields = ("assigned_to",)
    fields = ("description", "assigned_to", "due_date", "status", "is_paid_relevant")


# =================================================================
# Inline 2 : Inspection (Utilisé par Site)
# -> Déplacé ici pour être défini avant SiteInline
# =================================================================
class InspectionInline(admin.TabularInline):
    model = Inspection
    extra = 1
    raw_id_fields = ("inspector",)
    fields = (
        "type_inspection",
        "resultat",
        "date_inspection",
        "rapport_photos_url",
        "commentaires",
    )


# =================================================================
# Inline 3 : Site (Utilise TaskInline et InspectionInline)
# =================================================================
class SiteInline(admin.TabularInline):
    model = Site
    extra = 1
    raw_id_fields = ("team_lead",)
    # 🎉 CORRECTION : TaskInline et InspectionInline sont maintenant définis.
    inlines = [TaskInline, InspectionInline]
    fields = ("site_id_client", "name", "team_lead", "status")


# =================================================================
# 1. Admin du Modèle Project (AVEC ISOLATION)
# =================================================================
@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "country",
        "client_name",
        "coordinator",
        "start_date",
        "end_date",
    )
    list_filter = ("country", "client_name", "coordinator")
    search_fields = ("name", "client_name", "country__name", "country__code")
    raw_id_fields = ("country", "coordinator", "created_by")
    inlines = [SiteInline]

    # 💥 AJOUT : Afficher le type dans la liste et les filtres
    list_display = (
        "name",
        "project_type",
        "country",
        "coordinator",
        "progress_percentage",
        "start_date",
        "end_date",
        "is_active",
        "is_completed",
    )
    list_filter = (
        "country",
        "coordinator",
        "is_active",
        "is_completed",
        "project_type",
    )
    # ... (Reste des attributs) ...

    # 🔒 LOGIQUE D'ISOLATION : Filtre les projets visibles par pays d'affectation
    def get_queryset(self, request):
        qs = super().get_queryset(request)

        # Le Superuser voit tout
        if request.user.is_superuser:
            return qs

        # Filtre les objets selon les pays où l'utilisateur est actif
        active_country_ids = request.user.active_countries
        return qs.filter(country__id__in=active_country_ids)

    # Logique de traçabilité
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


# =================================================================
# 2. Admin du Modèle Site (AVEC ISOLATION ET DÉLÉGATION)
# =================================================================
@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    list_display = ("site_id_client", "name", "project", "team_lead", "status")
    list_filter = ('status', 'site_type', 'project__client__name')
    search_fields = ("site_id_client", "name", "project__name")
    raw_id_fields = ("project", "team_lead", "created_by")
    # Note : Le SiteAdmin n'utilise pas InspectionInline/TaskInline par défaut.
    # Pour afficher les tâches en liste séparée dans l'admin Site, vous pouvez ajouter TaskInline ici :
    inlines = [TaskInline]

    # 🔒 LOGIQUE D'ISOLATION : Filtre les sites visibles par pays d'affectation
    def get_queryset(self, request):
        qs = super().get_queryset(request)

        if request.user.is_superuser:
            return qs

        active_country_ids = request.user.active_countries
        # Le pays est récupéré via la FK du Project Parent
        return qs.filter(project__country__id__in=active_country_ids)

    # 🔑 LOGIQUE DE DÉLÉGATION : Le Country Manager peut éditer les sites
    def has_change_permission(self, request, obj=None):
        perm = super().has_change_permission(request, obj)

        if obj and not request.user.is_superuser:
            country_id = obj.project.country_id

            # Condition 1: Utilisateur est le coordinateur assigné au projet
            is_coordinator = obj.project.coordinator == request.user

            # Condition 2: Utilisateur est Country Manager du pays du projet (Délégation)
            is_country_manager = (
                request.user.has_role("Country Manager")
                and country_id in request.user.active_countries
            )

            # Seul le coordinateur, le CM, ou le superuser ont la permission de changer
            return perm and (is_coordinator or is_country_manager)

        return perm

    # Logique de traçabilité
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


# =================================================================
# 3. Admin du Modèle Task (AVEC ISOLATION)
# =================================================================
@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        "site_display",
        "description_short",
        "assigned_to",
        "due_date",
        "status",
    )
    list_filter = ("status", "is_paid_relevant", "site__project__country")
    search_fields = ("description", "site__site_id_client", "assigned_to__username")
    raw_id_fields = ("site", "assigned_to", "created_by")

    def site_display(self, obj):
        return f"{obj.site.project.country.code} - {obj.site.site_id_client}"

    site_display.short_description = "Pays/Site"

    def description_short(self, obj):
        return (
            obj.description[:75] + "..."
            if len(obj.description) > 75
            else obj.description
        )

    description_short.short_description = "Description"

    # 🔒 LOGIQUE D'ISOLATION : Filtre les tâches visibles par pays d'affectation
    def get_queryset(self, request):
        qs = super().get_queryset(request)

        if request.user.is_superuser:
            return qs

        # ✅ CORRECTION : Utilisation de la propriété active_country_ids
        active_country_ids = request.user.active_country_ids
        # Le pays est récupéré via Site -> Project
        return qs.filter(site__project__country__id__in=active_country_ids)

    # Logique de traçabilité
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


# =================================================================
# 4. Admin du Modèle Inspection (Final)
# =================================================================
@admin.register(Inspection)
class InspectionAdmin(admin.ModelAdmin):
    list_display = (
        "site",
        "type_inspection",
        "resultat_inspection",
        "date_inspection",
        "inspector",
    )
    list_filter = (
        "site",
        "type_inspection",
        "resultat_inspection",  # <-- CORRECTION (Était 'resultat')
        "inspector",
    )
    search_fields = ("site__site_id_client", "inspector__username")


# ADMIN POUR LES MODÈLES DE RÉFÉRENCE (Lookup Models)
# =================================================================


@admin.register(SitePhase)
class SitePhaseAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)
    list_editable = ("is_active",)


@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)
    list_editable = ("is_active",)


@admin.register(AntennaType)
class AntennaTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)
    list_editable = ("is_active",)


@admin.register(EnclosureType)
class EnclosureTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)
    list_editable = ("is_active",)


@admin.register(BBMLType)
class BBMLTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)
    list_editable = ("is_active",)


@admin.register(RadioType)
class RadioTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)
    list_editable = ("is_active",)


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)
    list_editable = ("is_active",)


# =================================================================
# ADMIN POUR SiteRadioConfiguration
# =================================================================


@admin.register(SiteRadioConfiguration)
class SiteRadioConfigurationAdmin(admin.ModelAdmin):

    list_display = ("site", "radio_type", "quantity")
    list_filter = ("radio_type", "site__project__country")
    search_fields = ("site__site_id_client", "radio_type__name")
    raw_id_fields = ("site",)


# =================================================================
# ADMINS POUR LES MODÈLES DE CONFIGURATION ET LIAISON
# =================================================================


@admin.register(SiteType)
class SiteTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")
    list_editable = ("is_active",)


@admin.register(InstallationType)
class InstallationTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")
    list_editable = ("is_active",)


@admin.register(TransmissionLink)
class TransmissionLinkAdmin(admin.ModelAdmin):
    list_display = ("link_id", "site_a", "site_b", "created_at")
    search_fields = ("link_id", "site_a__site_id_client", "site_b__site_id_client")


# =================================================================
# ADMIN POUR ProjectType (NOUVEAU)
# =================================================================
@admin.register(ProjectType)
class ProjectTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "is_transmission", "is_active")
    list_filter = ("is_transmission", "is_active")
    list_editable = ("is_transmission", "is_active")
    search_fields = ("name",)


# Ajoutez cette classe Admin
@admin.register(TaskType)
class TaskTypeAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "code",
        "category",
        "expected_duration_hours",
        "is_active",
        "order",
    )
    list_filter = ("category", "is_active")
    list_editable = ("order", "is_active", "expected_duration_hours")
    search_fields = ("name", "code", "description")
    ordering = ("category", "order")
