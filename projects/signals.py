# projects/signals.py

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import transaction  # ✅ AJOUT CRITIQUE pour la robustesse
from .models import Task


@receiver(post_save, sender=Task)
@receiver(post_delete, sender=Task)
def update_site_progress_on_task_change(sender, instance, **kwargs):
    """
    Met à jour la progression du site quand une tâche est modifiée ou supprimée.
    """
    if kwargs.get("raw", False):  # Ignore pendant le chargement des fixtures
        return

    if instance.site:
        # Utiliser transaction.on_commit pour éviter les deadlocks
        transaction.on_commit(lambda: instance.site.update_progress())
