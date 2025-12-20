# projects/urls.py (MODIFIÉ ET CORRIGÉ)

from django.urls import path
from django.shortcuts import render
from django.db.models import Q

from . import views
from .views import (
    ProjectListView,
    ProjectDetailView,
    TeamLeadTasksView,
    ProjectTableView,
    SiteDetailView, # 💡 AJOUT
)
from projects.models import Site, Task

app_name = "projects"


def debug_team_lead(request):
    user = request.user
    context = {
        "user": user,
        "sites_managed": Site.objects.filter(team_lead=user),
        "tasks_assigned": Task.objects.filter(assigned_to=user),
        "all_tasks": Task.objects.filter(Q(site__team_lead=user) | Q(assigned_to=user)),
    }
    return render(request, "projects/debug_team_lead.html", context)


urlpatterns = [
    # 1. LISTE ET DÉTAIL (MODIFIÉ)
    
    # ⬇️ La Vue Tableau (votre image) est maintenant la vue par défaut ("")
    path("", ProjectTableView.as_view(), name="project_table"),
    
    # ⬇️ La Vue Liste (l'ancienne) est maintenant sur "list/"
    path("list/", ProjectListView.as_view(), name="project_list"),
    
    path("<int:pk>/", ProjectDetailView.as_view(), name="project_detail"),
    
    # 2. INTERFACE CM : Création de Projet
    path("new/", views.ProjectCreateView.as_view(), name="project_create"),
    path(
        "<int:pk>/edit/", views.ProjectUpdateView.as_view(), name="project_update"
    ),
    
    # 3. INTERFACE COORDONNATEUR/CM : Création de Site
    path(
        "<int:project_pk>/site/new/", views.SiteCreateView.as_view(), name="site_create"
    ),
    path("site/<int:pk>/edit/", views.SiteUpdateView.as_view(), name="site_update"),
    path("site/<int:pk>/", SiteDetailView.as_view(), name="site_detail"),

    # 4. INTERFACE TÂCHES
    path(
        "site/<int:site_pk>/task/new/",
        views.TaskCreateView.as_view(),
        name="task_create",
    ),
    path(
        "task/<int:pk>/edit/", views.TaskUpdateView.as_view(), name="task_update"
    ), 
    path(
        "task/<int:pk>/photos/",
        views.TaskPhotoUploadView.as_view(),
        name="task_photo_upload",
    ), 
    path("task/<int:pk>/report/", views.TaskReportView.as_view(), name="task_report"),
    
    path(
        "task/<int:task_pk>/uninstallation-report/",
        views.UninstallationReportView.as_view(),
        name="uninstallation_report",
    ),

    path('task/photo/<int:pk>/delete/', views.task_photo_delete, name='task_photo_delete'),

    # 5. INTERFACE INSPECTION
    path(
        "site/<int:site_pk>/inspection/new/",
        views.InspectionCreateView.as_view(),
        name="inspection_create",
    ),
    
    # 6. INTERFACE TEAM LEAD
    path(
        "my-tasks/by-site/", TeamLeadTasksView.as_view(), name="team_lead_tasks_by_site"
    ),
    
    # 7. INTERFACE SPÉCIALE : Transmission
    path(
        "<int:project_pk>/transmission/new/",
        views.TransmissionLinkCreateView.as_view(),
        name="transmission_link_create",
    ), 
]