from django.db import migrations

def create_desinstallation_task_type(apps, schema_editor):
    TaskType = apps.get_model('projects', 'TaskType')
    TaskType.objects.create(
        name='Désinstallation',
        code='DESINSTALLATION',
        category='CLOSURE',
        description='Tâche pour enregistrer la désinstallation des équipements sur un site.'
    )

class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0026_uninstallationreport_uninstalledequipment'),
    ]

    operations = [
        migrations.RunPython(create_desinstallation_task_type),
    ]