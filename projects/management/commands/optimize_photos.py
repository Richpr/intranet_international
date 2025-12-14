# projects/management/commands/optimize_photos.py

from django.core.management.base import BaseCommand
from projects.models import TaskPhoto
from django.db import transaction

class Command(BaseCommand):
    help = 'Re-sauvegarde toutes les photos de tâche pour appliquer la compression/redimensionnement.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Démarrage de l\'optimisation des photos existantes...'))
        
        # Sélectionner toutes les instances de TaskPhoto
        photos = TaskPhoto.objects.all()
        total_photos = photos.count()
        count = 0
        
        # Utilisez transaction.atomic pour assurer la cohérence 
        with transaction.atomic():
            for photo in photos:
                try:
                    # 🚨 Ligne critique pour déclencher le save() optimisé
                    photo.photo.open() 
                    
                    # Appeler save() pour forcer l'optimisation
                    photo.save()
                    
                    # Mettre à jour la progression
                    count += 1
                    if count % 10 == 0:
                        self.stdout.write(f'  -> Photo {count}/{total_photos} optimisée...')
                        
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Erreur sur la photo ID {photo.pk}: {e}'))
                    pass 

        self.stdout.write(self.style.SUCCESS(
            f'Opération terminée. Total de {count} photos traitées (sur {total_photos}).'
        ))