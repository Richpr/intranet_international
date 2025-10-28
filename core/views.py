# core/views.py (Fusionné)

from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Prefetch, Count, Case, When
from datetime import date
import json

# 👇 IMPORTS AJOUTÉS DE MA PROPOSITION
from django.db.models import Sum, Avg, DecimalField
from django.db.models.functions import Coalesce
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from projects.models import Project, Task, Site
from finance.models import Depense, Revenu, DEPENSE_CATEGORIE_CHOICES, ObligationFiscale
from inventaire.models import Equipement
from logistique.models import Vehicule
from rh.models import Certification
# Note: J'utilise CustomUser car il est importé implicitement par 'settings.AUTH_USER_MODEL'
# mais j'ai besoin de 'Assignation'
from users.models import CustomUser, Assignation 


class HomeView(LoginRequiredMixin, TemplateView):
    template_name = "core/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # 👇 CORRECTION : J'utilise 'date.today()' comme tu l'as fait
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

        # --- 3. LOGIQUE SPÉCIFIQUE PAR RÔLE (EXISTANTE) ---
        # (J'ai laissé tout ton code existant intact ici)
        if IS_CM:
            cm_projects = Project.objects.filter(country__id__in=active_country_ids)
            cm_sites = Site.objects.filter(project__country__id__in=active_country_ids)
            
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
            my_tasks = personal_tasks
            context.update({
                "my_tasks": my_tasks,
                "my_active_tasks_count": my_tasks.count(),
                "my_overdue_tasks_count": my_tasks.filter(due_date__lt=today).count(),
                "my_completed_tasks_today": Task.objects.filter(
                    assigned_to=user, completion_date__date=today
                ).count(),
            })

        # ====================================================================
        # 4. NOUVEAU : CALCULS FINANCIERS & RH (de tache.txt) [Source: 7, 8, 13]
        # ====================================================================
        # Ces calculs ne s'exécuteront que si l'utilisateur est CM 
        # ou un rôle manager (à ajuster si besoin)
        if IS_CM or user.is_staff: # Tu peux changer cette condition
            
            trente_jours_ago = today - timedelta(days=30)
            
            # [Source 7] Calcul de la rentabilité par projet
            projets = Project.objects.filter(
                is_active=True, 
                country__id__in=active_country_ids
            ).annotate(
                total_depenses=Coalesce(
                    Sum('depenses__montant'), 
                    Decimal('0.00'),
                    output_field=DecimalField()
                )
            ).order_by('-start_date')
            
            rentabilite_projets = []
            for p in projets:
                budget_restant = p.budget_alloue - p.total_depenses
                rentabilite_projets.append({
                    'nom': p.name,
                    'budget_alloue': p.budget_alloue,
                    'total_depenses': p.total_depenses,
                    'budget_restant': budget_restant
                })
            
            context['rentabilite_projets'] = rentabilite_projets

            # [Source 8] Totaux des 30 derniers jours
            total_depenses_30j = Depense.objects.filter(
                date__gte=trente_jours_ago,
                projet_associe__country__id__in=active_country_ids
            ).aggregate(
                total=Coalesce(Sum('montant'), Decimal('0.00'))
            )['total']
            
            total_revenus_30j = Revenu.objects.filter(
                date__gte=trente_jours_ago,
                projet_facture__country__id__in=active_country_ids
            ).aggregate(
                total=Coalesce(Sum('montant'), Decimal('0.00'))
            )['total']
            
            context['total_depenses_30j'] = total_depenses_30j
            context['total_revenus_30j'] = total_revenus_30j
            context['balance_30j'] = total_revenus_30j - total_depenses_30j

            # [Source 8] Dépenses par catégorie
            depenses_par_categorie = Depense.objects.filter(
                date__gte=trente_jours_ago,
                projet_associe__country__id__in=active_country_ids
            ).values('categorie').annotate(
                total=Sum('montant')
            ).order_by('-total')
            
            
            categorie_choices = dict(DEPENSE_CATEGORIE_CHOICES)
            context['depenses_par_categorie'] = [
                {'categorie': categorie_choices.get(d['categorie'], d['categorie']), 'total': d['total']}
                for d in depenses_par_categorie
            ]

            # [Source 12, 13] Coût d'inactivité
            # ÉTAPE 1: (NOUVELLE LIGNE) Récupère d'abord les employés des bons pays
            
            # Ligne ~205 (Corrigée)
            # On utilise la liaison 'assignments' pour joindre le pays
            employes_in_active_countries = CustomUser.objects.filter(
                assignments__country__id__in=active_country_ids,
                assignments__is_active=True # Assurons-nous que l'affectation au pays est active
            ).distinct() # Important pour éviter les doublons


            # ÉTAPE 2: (LIGNE 204 MODIFIÉE) Utilise ce queryset pour filtrer les assignations
            employes_assignes_ids = Assignation.objects.filter(
                date_debut_assignation__lte=today,
                date_fin_assignation__gte=today,
                employe__in=employes_in_active_countries  # <-- On utilise __in sur la liste d'employés
            ).values_list('employe_id', flat=True).distinct()

            employes_inactifs = CustomUser.objects.filter(
                statut_actuel='ACTIF',
                assignments__country__id__in=active_country_ids, # <-- CORRECTION
                assignments__is_active=True                      # <-- AJOUT IMPORTANT
            ).exclude(
                id__in=employes_assignes_ids
            ).distinct() # <-- AJOUT IMPORTANT

            cout_inactivite = employes_inactifs.aggregate(
                total=Coalesce(Sum('salaire_mensuel_base'), Decimal('0.00'))
            )['total']
            
            context['employes_non_assignes'] = employes_inactifs
            context['cout_inactivite_mensuel'] = cout_inactivite

            # [Source 14, 15] Suivi des Tâches Global (pour CM)
            taches_globales = Task.objects.filter(site__project__country__id__in=active_country_ids)
            
            context['taches_en_retard'] = taches_globales.filter(
                due_date__lt=today
            ).exclude(
                status='COMPLETED'
            ).count()
            
            context['taches_bloquees'] = taches_globales.filter(status='BLOCKED').count()

            # New stats from inventaire, logistique, rh
            context['equipement_count'] = Equipement.objects.count()
            context['vehicule_count'] = Vehicule.objects.count()
            context['expiring_certifications_count'] = Certification.objects.filter(date_expiration__lte=today + timedelta(days=30)).count()
            context['upcoming_obligations_count'] = ObligationFiscale.objects.filter(date_echeance__gte=today, statut='A_PAYER').count()

        return context