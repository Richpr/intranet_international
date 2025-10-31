from django.urls import path
from . import views

app_name = 'reporting'

urlpatterns = [
    path('ran-sites/', views.ran_site_list_view, name='ran_site_list'),
    path('ran-sites/pdf/', views.ran_site_list_pdf, name='ran_site_list_pdf'),
    path('ran-sites/excel/', views.ran_site_list_excel, name='ran_site_list_excel'),
    path('transmission-sites/', views.transmission_site_list_view, name='transmission_site_list'),
    path('transmission-sites/pdf/', views.transmission_site_list_pdf, name='transmission_site_list_pdf'),
    path('transmission-sites/excel/', views.transmission_site_list_excel, name='transmission_site_list_excel'),
    path('survey-sites/', views.survey_site_list_view, name='survey_site_list'),
    path('survey-sites/pdf/', views.survey_site_list_pdf, name='survey_site_list_pdf'),
    path('survey-sites/excel/', views.survey_site_list_excel, name='survey_site_list_excel'),

    path('site-profitability/', views.site_profitability_report_view, name='site_profitability_report'),

    path('cost-per-vehicle/', views.cost_per_vehicle_report_view, name='cost_per_vehicle_report'),

    path('inventory-status/', views.inventory_status_report_view, name='inventory_status_report'),
    path('performance-annuelle/', views.performance_annuelle_view, name='performance_annuelle'),
]
