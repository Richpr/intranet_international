# finance/signals.py

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.db import models  # Nécessaire pour models.Sum
from .models import WorkCompletionRecord, SalaryStructure
from projects.models import Task

# =================================================================
# 1. Signal PRE_SAVE : Calculer le Coût (Paie)
# =================================================================


@receiver(pre_save, sender=WorkCompletionRecord)
def calculate_work_record_cost(sender, instance, **kwargs):
    """
    Calcule le coût total de l'enregistrement de travail basé sur le taux horaire de l'employé
    et la structure salariale active pour son pays/rôle.
    """

    # Le calcul est effectué uniquement si la durée est positive et l'enregistrement n'est pas encore payé.
    if (
        instance.duration_hours is not None
        and instance.duration_hours > 0
        and not instance.is_paid_out
    ):

        # 1. Obtenir l'Employé et son Rôle/Pays actif
        employee = (
            instance.employee
        )  # 💡 CORRECTION : Utiliser 'employee' au lieu de 'user'

        # On suppose que l'Employé de terrain a une affectation principale active.
        # On utilise le même principe que dans les vues : prendre la première affectation active.
        active_assignment = employee.assignments.filter(is_active=True).first()

        if not active_assignment:
            # Si l'employé n'a pas d'affectation active pour calculer le coût
            instance.hourly_rate_used = 0
            instance.cost = 0
            return

        try:
            # 2. Trouver la structure salariale pour ce Pays et ce Rôle
            salary_structure = SalaryStructure.objects.get(
                country=active_assignment.country, role=active_assignment.role
            )

            # 3. Calculer le taux horaire
            base_salary_decimal = salary_structure.base_amount
            HOURS_PER_MONTH = 160  # Hypothèse : 160 heures par mois (20 jours * 8h)

            # Gérer la division par zéro
            if HOURS_PER_MONTH == 0:
                hourly_rate = 0
            else:
                hourly_rate = base_salary_decimal / HOURS_PER_MONTH

            # 4. Assigner le taux et le coût à l'enregistrement
            instance.hourly_rate_used = hourly_rate
            instance.cost = instance.duration_hours * hourly_rate

        except SalaryStructure.DoesNotExist:
            # Si aucune structure salariale n'est définie pour ce couple Pays/Rôle
            instance.hourly_rate_used = 0
            instance.cost = 0


# =================================================================
# 2. Signal POST_SAVE : Mettre à jour la Progression
# =================================================================


@receiver(post_save, sender=WorkCompletionRecord)
def update_task_progress(sender, instance, created, **kwargs):
    """
    Met à jour le champ progress_percentage de la tâche après
    chaque enregistrement d'achèvement de travail.
    """

    task = instance.task

    # 1. Calculer la progression totale enregistrée
    total_completion = WorkCompletionRecord.objects.filter(task=task).aggregate(
        total_percentage=models.Sum("completion_percentage")
    )["total_percentage"]

    if total_completion is None:
        total_completion = 0

    # 2. Limiter la progression à 100%
    new_progress = min(100, total_completion)

    # 3. Mettre à jour la tâche pour éviter une boucle infinie de signaux post_save
    # on utilise .update() qui saute la méthode save() du modèle.
    Task.objects.filter(pk=task.pk).update(progress_percentage=new_progress)
