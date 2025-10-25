# projects/signals.py

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import transaction  # ✅ AJOUT CRITIQUE pour la robustesse
from .models import Task


@receiver(post_save, sender=Task)
def update_site_and_project_progress(sender, instance, **kwargs):
    """
    Signal déclenché après la sauvegarde (création ou mise à jour) d'une Tâche.
    Il appelle la méthode update_progress() du Site parent, qui cascade vers le Projet.
    """

    # Évite de déclencher le signal pendant des opérations de chargement initial (ex: fixtures)
    if kwargs.get("raw", False):
        return

    # Vérifie si le site existe et n'est pas None
    if instance.site:
        # ✅ CORRECTION : Assurer l'atomicité pour éviter les race conditions
        with transaction.atomic():
            instance.site.update_progress()


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
