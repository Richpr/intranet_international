# finance/apps.py

from django.apps import AppConfig


class FinanceConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "finance"
    verbose_name = "3. Finances & Paie"

    # AJOUTER CETTE MÉTHODE
    def ready(self):
        # Importer les signaux pour les connecter
        pass
