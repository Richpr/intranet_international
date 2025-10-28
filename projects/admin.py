from django.contrib import admin
from .models import Project, Site, Task, TaskPhoto, Inspection, TransmissionLink, ProjectType, SitePhase, Batch, AntennaType, EnclosureType, BBMLType, RadioType, Client, SiteRadioConfiguration, SiteType, InstallationType, TaskResultType, TaskType
from users.admin import AssignationInline


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    inlines = [AssignationInline]
    list_display = ('name', 'country', 'client', 'statut', 'budget_alloue')
    list_filter = ('country', 'client', 'statut')
    search_fields = ('name',)


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