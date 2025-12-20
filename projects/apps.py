from django.apps import AppConfig


class ProjectsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "projects"

    # 💡 AJOUT CRITIQUE : Connecter les signaux
    def ready(self):
        pass
