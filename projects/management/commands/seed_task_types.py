from django.core.management.base import BaseCommand
from projects.models import TaskType, TaskResultType


class Command(BaseCommand):
    help = "Crée les types de tâches initiaux"

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS("Démarrage du script de création des types de tâches...")
        )

        try:
            # Récupérer les types de résultats (assurez-vous qu'ils existent via une migration data ou un autre seeder)
            ftr = TaskResultType.objects.get(code="FTR")
            nftr = TaskResultType.objects.get(code="NFTR")
            done = TaskResultType.objects.get(code="DONE")
            not_done = TaskResultType.objects.get(code="NOT_DONE")
            aligned = TaskResultType.objects.get(code="ALIGNED")
            misaligned = TaskResultType.objects.get(code="MISALIGNED")
            integrated = TaskResultType.objects.get(code="INTEGRATED")
            integration_failed = TaskResultType.objects.get(code="INTEGRATION_FAILED")
        except TaskResultType.DoesNotExist as e:
            self.stderr.write(
                self.style.ERROR(
                    f"Erreur: Un type de résultat requis n'existe pas. Assurez-vous que TaskResultType est déjà peuplé. Détail: {e}"
                )
            )
            return  # Sortir si les prérequis sont manquants

        # La liste de données est nommée 'task_types'
        task_types = [
            # QUALITÉ (QA) - Requiert photos
            {
                "name": "QA Photos Quality",
                "code": "QA_PHOTOS",
                "category": "QUALITY",
                "order": 1,
                "expected_duration_hours": 2,
                "requires_photos": True,
                "photo_instructions": "Prendre des photos de: 1. Vue générale 2. Détails d'installation 3. Câblage",
                "result_types": [ftr, nftr],
            },
            {
                "name": "Contrôle Qualité Final",
                "code": "FINAL_QA",
                "category": "QUALITY",
                "order": 2,
                "expected_duration_hours": 3,
                "requires_photos": True,
                "result_types": [ftr, nftr],
            },
            # ALIGNEMENT - Requiert photos
            {
                "name": "Alignement Antenne",
                "code": "ANTENNA_ALIGNMENT",
                "category": "ALIGNMENT",
                "order": 1,
                "expected_duration_hours": 4,
                "requires_photos": True,
                "photo_instructions": "Photos de: 1. Outils d'alignement 2. Écran de mesure 3. Antenne alignée",
                "result_types": [aligned, misaligned],
            },
            # INTÉGRATION
            {
                "name": "Intégration Réseau",
                "code": "NETWORK_INTEGRATION",
                "category": "INTEGRATION",
                "order": 1,
                "expected_duration_hours": 6,
                "requires_photos": False,
                "result_types": [integrated, integration_failed],
            },
            {
                "name": "Test Intégration Système",
                "code": "SYSTEM_INTEGRATION",
                "category": "INTEGRATION",
                "order": 2,
                "expected_duration_hours": 4,
                "requires_photos": False,
                "result_types": [done, not_done],
            },
            # SÉCURITÉ (EHS) - Requiert photos
            {
                "name": "Audit EHS",
                "code": "EHS_AUDIT",
                "category": "SAFETY",
                "order": 1,
                "expected_duration_hours": 3,
                "requires_photos": True,
                "photo_instructions": "Photos de: 1. Équipement de sécurité 2. Zone de travail 3. Signalisation",
                "result_types": [ftr, nftr],
            },
            # TESTS
            {
                "name": "IMK Test",
                "code": "IMK",
                "category": "TESTING",
                "order": 1,
                "expected_duration_hours": 2,
                "requires_photos": False,
                "result_types": [done, not_done],
            },
            {
                "name": "SRS Test",
                "code": "SRS",
                "category": "TESTING",
                "order": 2,
                "expected_duration_hours": 2,
                "requires_photos": False,
                "result_types": [done, not_done],
            },
            # PRÉPARATION (Ajout des champs manquants pour uniformité)
            {
                "name": "Survey Site",
                "code": "SURVEY",
                "category": "PREPARATION",
                "order": 1,
                "expected_duration_hours": 4,
                "requires_photos": False,
                "result_types": [done, not_done],
            },
            {
                "name": "Planning Installation",
                "code": "PLANNING",
                "category": "PREPARATION",
                "order": 2,
                "expected_duration_hours": 2,
                "requires_photos": False,
                "result_types": [done, not_done],
            },
            {
                "name": "Commandes Matériel",
                "code": "MATERIAL_ORDER",
                "category": "PREPARATION",
                "order": 3,
                "expected_duration_hours": 1,
                "requires_photos": False,
                "result_types": [done, not_done],
            },
            # INSTALLATION (Ajout des champs manquants pour uniformité)
            {
                "name": "Installation Antenne",
                "code": "ANTENNA_INSTALL",
                "category": "INSTALLATION",
                "order": 1,
                "expected_duration_hours": 6,
                "requires_photos": True,
                "result_types": [done, not_done],
            },
            {
                "name": "Installation RRH",
                "code": "RRH_INSTALL",
                "category": "INSTALLATION",
                "order": 2,
                "expected_duration_hours": 4,
                "requires_photos": True,
                "result_types": [done, not_done],
            },
            {
                "name": "Installation BBU",
                "code": "BBU_INSTALL",
                "category": "INSTALLATION",
                "order": 3,
                "expected_duration_hours": 4,
                "requires_photos": True,
                "result_types": [done, not_done],
            },
            {
                "name": "Câblage Fibre",
                "code": "FIBER_CABLING",
                "category": "INSTALLATION",
                "order": 4,
                "expected_duration_hours": 3,
                "requires_photos": True,
                "result_types": [done, not_done],
            },
            {
                "name": "Câblage Alimentation",
                "code": "POWER_CABLING",
                "category": "INSTALLATION",
                "order": 5,
                "expected_duration_hours": 4,
                "requires_photos": True,
                "result_types": [done, not_done],
            },
            # SÉCURITÉ (Ajout des champs manquants pour uniformité)
            {
                "name": "EHS Pré-Installation",
                "code": "EHS_PRE",
                "category": "SAFETY",
                "order": 1,
                "expected_duration_hours": 2,
                "requires_photos": True,
                "result_types": [done, not_done],
            },
            {
                "name": "EHS Pendant Installation",
                "code": "EHS_DURING",
                "category": "SAFETY",
                "order": 2,
                "expected_duration_hours": 1,
                "requires_photos": True,
                "result_types": [done, not_done],
            },
            {
                "name": "EHS Post-Installation",
                "code": "EHS_POST",
                "category": "SAFETY",
                "order": 3,
                "expected_duration_hours": 2,
                "requires_photos": True,
                "result_types": [done, not_done],
            },
            # TESTS (Ajout des champs manquants pour uniformité et codes uniques pour éviter les doublons)
            {
                "name": "Test Intégration",
                "code": "INTEGRATION_TEST",
                "category": "TESTING",
                "order": 1,
                "expected_duration_hours": 4,
                "requires_photos": False,
                "result_types": [done, not_done],
            },
            {
                "name": "ATP Client",
                "code": "ATP",
                "category": "TESTING",
                "order": 2,
                "expected_duration_hours": 3,
                "requires_photos": False,
                "result_types": [done, not_done],
            },
            # Codes SRS et IMK déjà utilisés plus haut, on les rend uniques ici
            {
                "name": "SRS Supplémentaire",
                "code": "SRS_2",
                "category": "TESTING",
                "order": 3,
                "expected_duration_hours": 2,
                "requires_photos": False,
                "result_types": [done, not_done],
            },
            {
                "name": "IMK Supplémentaire",
                "code": "IMK_2",
                "category": "TESTING",
                "order": 4,
                "expected_duration_hours": 2,
                "requires_photos": False,
                "result_types": [done, not_done],
            },
            # CLÔTURE (Ajout des champs manquants pour uniformité)
            {
                "name": "Nettoyage Site",
                "code": "CLEANUP",
                "category": "CLOSURE",
                "order": 1,
                "expected_duration_hours": 2,
                "requires_photos": True,
                "result_types": [done, not_done],
            },
            {
                "name": "Documentation Finale",
                "code": "FINAL_DOC",
                "category": "CLOSURE",
                "order": 2,
                "expected_duration_hours": 3,
                "requires_photos": False,
                "result_types": [done, not_done],
            },
        ]

        # CORRECTION DU NAMEERROR : La liste s'appelle 'task_types', pas 'task_types_data'
        for task_data in task_types:

            # Utilisation de .pop() pour extraire la liste des types de résultats
            result_types = task_data.pop("result_types", [])

            # Définition des valeurs par défaut pour les champs spécifiques
            requires_photos = task_data.get("requires_photos", False)
            photo_instructions = task_data.get("photo_instructions", "")

            # Créer ou mettre à jour le TaskType
            task_type, created = TaskType.objects.get_or_create(
                code=task_data["code"],
                defaults={
                    "name": task_data["name"],
                    "category": task_data["category"],
                    "order": task_data["order"],
                    "expected_duration_hours": task_data["expected_duration_hours"],
                    "requires_photos": requires_photos,
                    "photo_instructions": photo_instructions,
                },
            )

            # Associer les types de résultats (uniquement si l'objet vient d'être créé ou si on veut s'assurer des liens)
            if created:
                for result_type in result_types:
                    task_type.allowed_result_types.add(result_type)

                self.stdout.write(
                    self.style.SUCCESS(f"Type de tâche créé: {task_type.name}")
                )
            else:
                self.stdout.write(
                    self.style.NOTICE(
                        f"Type de tâche déjà existant: {task_type.name} (Mis à jour/Sauté)"
                    )
                )

        self.stdout.write(self.style.SUCCESS("Création des types de tâches terminée."))
