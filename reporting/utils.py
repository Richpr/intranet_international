from projects.models import Project, Site
from django.db.models import Sum, Count, F
from django.db.models.functions import ExtractYear
from decimal import Decimal

def get_project_performance_by_year(country_id=None):
    """Agrège les données de performance des projets par année."""
    projects = Project.objects.all()
    if country_id:
        projects = projects.filter(country_id=country_id)

    performance_data = (
        projects.annotate(year=ExtractYear('start_date'))
        .values('year')
        .annotate(
            total_budget=Sum('budget_alloue'),
            total_progress=Sum('progress_percentage')
        )
        .order_by('year')
    )
    return performance_data

def get_site_completion_rate_by_year(country_id=None):
    """Agrège les données de complétion des sites par année."""
    sites = Site.objects.filter(status='COMPLETED')
    if country_id:
        sites = sites.filter(project__country_id=country_id)

    completion_data = (
        sites.annotate(year=ExtractYear('end_date'))
        .values('year')
        .annotate(completed_sites=Count('id'))
        .order_by('year')
    )
    return completion_data

def get_site_profitability_by_year(country_id=None):
    """Agrège les données de rentabilité des sites par année."""
    sites = Site.objects.filter(po_recu=True)
    if country_id:
        sites = sites.filter(project__country_id=country_id)

    profitability_data = (
        sites.annotate(year=ExtractYear('project__start_date'))
        .values('year')
        .annotate(total_revenue=Sum('prix_facturation'))
        .order_by('year')
    )
    return profitability_data
