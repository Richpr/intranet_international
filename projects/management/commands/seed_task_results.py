from django.core.management.base import BaseCommand
from projects.models import TaskResultType


class Command(BaseCommand):
    help = "Crée les types de résultats initiaux"

    def handle(self, *args, **options):
        result_types = [
            # Résultats de qualité (EHS, QA)
            {"name": "First Time Right (FTR)", "code": "FTR", "is_success": True},
            {
                "name": "Not First Time Right (NFTR)",
                "code": "NFTR",
                "is_success": False,
            },
            {"name": "First Time Pass (FTP)", "code": "FTP", "is_success": True},
            {"name": "Not First Time Pass (NFTP)", "code": "NFTP", "is_success": False},
            # Résultats binaires
            {"name": "Terminé (DONE)", "code": "DONE", "is_success": True},
            {"name": "Non Terminé (NOT_DONE)", "code": "NOT_DONE", "is_success": False},
            {"name": "Réussi (PASS)", "code": "PASS", "is_success": True},
            {"name": "Échoué (FAIL)", "code": "FAIL", "is_success": False},
            # Résultats d'alignement
            {"name": "Aligné avec Succès", "code": "ALIGNED", "is_success": True},
            {"name": "Alignement Échoué", "code": "MISALIGNED", "is_success": False},
            # Résultats d'intégration
            {"name": "Intégration Réussie", "code": "INTEGRATED", "is_success": True},
            {
                "name": "Intégration Échouée",
                "code": "INTEGRATION_FAILED",
                "is_success": False,
            },
        ]

        for result_data in result_types:
            result_type, created = TaskResultType.objects.get_or_create(
                code=result_data["code"], defaults=result_data
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f"Type de résultat créé: {result_type.name}")
                )
