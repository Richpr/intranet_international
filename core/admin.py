from django.contrib import admin
from .models import Departement

@admin.register(Departement)
class DepartementAdmin(admin.ModelAdmin):
    list_display = ('name', 'country', 'is_active')
    list_filter = ('country', 'is_active')
    search_fields = ('name', 'country__name')