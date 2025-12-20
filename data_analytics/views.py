from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .utils import (
    get_monthly_site_creation_data,
    get_monthly_expense_data,
    get_yearly_revenue_data,
    get_employee_performance_data,
    get_yearly_site_creation_data,
    get_team_lead_performance_data,
    get_site_creation_pivot_data,
)
from users.models import Country
from datetime import date
import calendar

@login_required
def dashboard_view(request):
    countries = Country.objects.filter(is_active=True)
    selected_country_id = request.GET.get('country')
    selected_year = request.GET.get('year', date.today().year)

    monthly_site_creation_qs = get_monthly_site_creation_data(selected_country_id, selected_year)
    monthly_expense_qs = get_monthly_expense_data(selected_country_id, selected_year)
    yearly_revenue_qs = get_yearly_revenue_data(selected_country_id)
    yearly_site_creation_qs = get_yearly_site_creation_data(selected_country_id)
    site_creation_pivot_data = get_site_creation_pivot_data(selected_country_id)
    employee_performance = get_employee_performance_data(selected_country_id)
    team_lead_performance = get_team_lead_performance_data(selected_country_id)

    monthly_site_creation = [
        {'month': item['month'], 'site_count': item['site_count']}
        for item in monthly_site_creation_qs
    ]
    monthly_expense = [
        {'month': item['month'], 'total_expense': float(item['total_expense']) if item['total_expense'] else 0}
        for item in monthly_expense_qs
    ]
    yearly_revenue = [
        {'year': item['year'], 'total_revenue': float(item['total_revenue']) if item['total_revenue'] else 0}
        for item in yearly_revenue_qs
    ]
    yearly_site_creation = [
        {'year': item['year'], 'site_count': item['site_count']}
        for item in yearly_site_creation_qs
    ]

    context = {
        'countries': countries,
        'selected_country_id': selected_country_id,
        'selected_year': selected_year,
        'years': range(date.today().year, date.today().year - 5, -1),
        'month_names': [calendar.month_name[i] for i in range(1, 13)],
        'monthly_site_creation': monthly_site_creation,
        'monthly_expense': monthly_expense,
        'yearly_revenue': yearly_revenue,
        'yearly_site_creation': yearly_site_creation,
        'site_creation_pivot_data': site_creation_pivot_data,
        'employee_performance': employee_performance,
        'team_lead_performance': team_lead_performance,
    }

    return render(request, 'data_analytics/dashboard.html', context)