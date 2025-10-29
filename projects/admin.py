from django.contrib import admin
from .models import (
    Project, Site, Task, TaskPhoto, Inspection, TransmissionLink,
    ProjectType, SitePhase, Batch, AntennaType, EnclosureType, BBMLType,
    RadioType, Client, SiteRadioConfiguration, SiteType, InstallationType,
    TaskResultType, TaskType, UninstallationReport, UninstalledEquipment
)
from users.admin import AssignationInline


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    inlines = [AssignationInline]
    list_display = ('name', 'country', 'client', 'statut', 'budget_alloue')
    list_filter = ('country', 'client', 'statut')
    search_fields = ('name',)


class UninstalledEquipmentInline(admin.TabularInline):
    model = UninstalledEquipment
    extra = 1


@admin.register(UninstallationReport)
class UninstallationReportAdmin(admin.ModelAdmin):
    inlines = [UninstalledEquipmentInline]
    list_display = ('task', 'storage_location', 'report_date', 'created_by')
    list_filter = ('report_date', 'storage_location')
    search_fields = ('task__site__name',)


admin.site.register(Site)
admin.site.register(Task)
admin.site.register(TaskPhoto)
admin.site.register(Inspection)
admin.site.register(TransmissionLink)
admin.site.register(ProjectType)
admin.site.register(SitePhase)
admin.site.register(Batch)
admin.site.register(AntennaType)
admin.site.register(EnclosureType)
admin.site.register(BBMLType)
admin.site.register(RadioType)
admin.site.register(Client)
admin.site.register(SiteRadioConfiguration)
admin.site.register(SiteType)
admin.site.register(InstallationType)
admin.site.register(TaskResultType)
admin.site.register(TaskType)
admin.site.register(UninstalledEquipment)