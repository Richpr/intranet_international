from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from projects.models import Project, Site, Task
from django.db.models import Q, Prefetch, Count, Case, When
from datetime import date
import json


class HomeView(LoginRequiredMixin, TemplateView):
    template_name = "core/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        today = date.today()
        context["today"] = today

        # --- 1. DONNÉES DE BASE CENTRALISÉES ---
        active_country_ids = user.active_country_ids
        context["main_role"] = user.main_role
        context["user_countries"] = user.active_countries_objects

        # Booléens de rôle pour la logique d'affichage
        IS_CM = user.is_cm
        IS_COORDINATOR = user.is_coordinator
        IS_TEAM_LEAD = user.is_team_lead
        IS_FIELD_TEAM = user.is_field_team

        context.update({
            "is_cm": IS_CM,
            "is_coordinator": IS_COORDINATOR,
            "is_team_lead": IS_TEAM_LEAD,
            "is_field_team": IS_FIELD_TEAM,
        })

        # --- 2. DONNÉES PERSONNELLES (POUR TOUS) ---
        personal_tasks = Task.objects.filter(
            assigned_to=user,
            status__in=["TO_DO", "IN_PROGRESS", "QC_PENDING"],
            site__project__country__id__in=active_country_ids,
        ).select_related("site__project__country").order_by("due_date")
        context["personal_tasks"] = personal_tasks

        # --- 3. LOGIQUE SPÉCIFIQUE PAR RÔLE ---

        if IS_CM:
            cm_projects = Project.objects.filter(country__id__in=active_country_ids)
            cm_sites = Site.objects.filter(project__country__id__in=active_country_ids)
            
            # Données pour le graphique de statut des projets
            status_counts = cm_projects.aggregate(
                active=Count(Case(When(is_active=True, is_completed=False, then=1))),
                completed=Count(Case(When(is_completed=True, then=1))),
                inactive=Count(Case(When(is_active=False, is_completed=False, then=1))),
            )
            context["project_status_chart_data"] = json.dumps({
                "labels": ["Actifs", "Terminés", "Inactifs"],
                "data": [status_counts['active'], status_counts['completed'], status_counts['inactive']],
            })

            context["cm_stats"] = {
                "total_projects": cm_projects.count(),
                "total_sites": cm_sites.count(),
                "sites_ftr": cm_sites.filter(last_inspection_result="FTR").count(),
                "sites_n_ftr": cm_sites.filter(last_inspection_result="N-FTR").count(),
            }

        if IS_COORDINATOR:
            coordinator_projects = Project.objects.filter(
                coordinator=user, country__id__in=active_country_ids
            )
            sites_in_projects = Site.objects.filter(project__in=coordinator_projects)
            sites_to_plan = sites_in_projects.filter(tasks__isnull=True)
            context.update({
                "coordinator_project_count": coordinator_projects.count(),
                "coordinator_sites_count": sites_in_projects.count(),
                "sites_to_plan_count": sites_to_plan.count(),
                "sites_to_plan": sites_to_plan.select_related("project__country", "team_lead")[:5],
            })

        if IS_TEAM_LEAD:
            active_tasks_prefetch = Prefetch(
                "tasks",
                queryset=Task.objects.filter(status__in=["TO_DO", "IN_PROGRESS", "QC_PENDING"]),
                to_attr="active_tasks_list",
            )
            tl_assigned_sites = (
                Site.objects.filter(
                    team_lead=user, project__country__id__in=active_country_ids
                )
                .select_related("project__country")
                .prefetch_related(active_tasks_prefetch)
                .order_by("project__name", "site_id_client")
            )

            tl_active_tasks_count = 0
            tl_overdue_tasks_count = 0
            for site in tl_assigned_sites:
                tl_active_tasks_count += len(site.active_tasks_list)
                for task in site.active_tasks_list:
                    if task.due_date < today:
                        tl_overdue_tasks_count += 1

            context.update({
                "tl_assigned_sites": tl_assigned_sites,
                "tl_assigned_sites_count": tl_assigned_sites.count(),
                "tl_active_tasks_count": tl_active_tasks_count,
                "tl_overdue_tasks_count": tl_overdue_tasks_count,
            })

        if IS_FIELD_TEAM:
            # my_tasks est déjà calculé dans la section "personnel"
            my_tasks = personal_tasks
            context.update({
                "my_tasks": my_tasks,
                "my_active_tasks_count": my_tasks.count(),
                "my_overdue_tasks_count": my_tasks.filter(due_date__lt=today).count(),
                "my_completed_tasks_today": Task.objects.filter(
                    assigned_to=user, completion_date__date=today
                ).count(),
            })

        return context
