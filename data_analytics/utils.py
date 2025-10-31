from django.db.models import Count, Sum, Avg
from django.db.models.functions import ExtractYear, ExtractMonth
from projects.models import Site
from finance.models import Depense, Revenu
from users.models import CustomUser

def get_monthly_site_creation_data(country_id=None, year=None):
    """Agrège les données de création de sites par mois."""
    sites = Site.objects.all()
    if country_id:
        sites = sites.filter(project__country_id=country_id)
    if year:
        sites = sites.filter(start_date__year=year)

    monthly_data = (
        sites.annotate(month=ExtractMonth('start_date'))
        .values('month')
        .annotate(site_count=Count('id'))
        .order_by('month')
    )
    return monthly_data

def get_monthly_expense_data(country_id=None, year=None):
    """Agrège les données de dépenses par mois."""
    expenses = Depense.objects.all()
    if country_id:
        expenses = expenses.filter(projet_associe__country_id=country_id)
    if year:
        expenses = expenses.filter(date__year=year)

    monthly_data = (
        expenses.annotate(month=ExtractMonth('date'))
        .values('month')
        .annotate(total_expense=Sum('montant'))
        .order_by('month')
    )
    return monthly_data

def get_yearly_revenue_data(country_id=None):
    """Agrège les données de revenus par année."""
    revenues = Revenu.objects.all()
    if country_id:
        revenues = revenues.filter(projet_facture__country_id=country_id)

    yearly_data = (
        revenues.annotate(year=ExtractYear('date'))
        .values('year')
        .annotate(total_revenue=Sum('montant'))
        .order_by('year')
    )
    return yearly_data

def get_yearly_site_creation_data(country_id=None):
    """Agrège les données de création de sites par année."""
    sites = Site.objects.all()
    if country_id:
        sites = sites.filter(project__country_id=country_id)

    yearly_data = (
        sites.annotate(year=ExtractYear('start_date'))
        .values('year')
        .annotate(site_count=Count('id'))
        .order_by('year')
    )
    return yearly_data

def get_team_lead_performance_data(country_id=None):
    """Récupère les données de performance des chefs d'équipe."""
    team_leads = CustomUser.objects.filter(groups__name='Team_Lead')
    if country_id:
        team_leads = team_leads.filter(assignments__country_id=country_id).distinct()

    performance_data = []
    for lead in team_leads:
        completed_sites = Site.objects.filter(team_lead=lead, status='COMPLETED').count()
        performance_data.append({
            'username': lead.username,
            'completed_sites': completed_sites,
            'success_rate': lead.team_lead_success_rate(),
        })
    return performance_data

def get_site_creation_by_year_and_month(country_id=None):
    """Agrège les données de création de sites par année et par mois."""
    sites = Site.objects.all()
    if country_id:
        sites = sites.filter(project__country_id=country_id)

    yearly_monthly_data = (
        sites.annotate(year=ExtractYear('start_date'), month=ExtractMonth('start_date'))
        .values('year', 'month')
        .annotate(site_count=Count('id'))
        .order_by('-year', '-month')
    )
    return yearly_monthly_data

def get_site_creation_pivot_data(country_id=None):
    """Crée un tableau croisé dynamique des données de création de sites."""
    data = get_site_creation_by_year_and_month(country_id)
    
    pivot_data = {}
    for item in data:
        year = item['year']
        month = item['month']
        site_count = item['site_count']
        
        if year not in pivot_data:
            pivot_data[year] = {m: 0 for m in range(1, 13)}
            pivot_data[year]['total'] = 0
        
        pivot_data[year][month] = site_count
        pivot_data[year]['total'] += site_count
        
    return pivot_data





def get_employee_performance_data(country_id=None, year=None, month=None):
    """Récupère les données de performance des employés."""
    users = CustomUser.objects.all()
    if country_id:
        users = users.filter(assignments__country_id=country_id).distinct()

    # This is a simplified version. For a more accurate calculation, 
    # you would need to filter tasks based on the provided year and month.
    performance_data = []
    for user in users:
        performance_data.append({
            'username': user.username,
            'main_role': user.main_role,
            'technician_completion_rate': user.technician_completion_rate(),
            'team_lead_success_rate': user.team_lead_success_rate(),
            'coordinator_on_time_completion_rate': user.coordinator_on_time_completion_rate(),
        })
    return performance_data
