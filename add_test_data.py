import os
import django
from datetime import date

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from projects.models import Project, Site, ProjectType, Client  # noqa: E402
from users.models import Country  # noqa: E402
from finance.models import Depense, Revenu  # noqa: E402
from users.models import CustomUser  # noqa: E402


def add_test_data():
    # Get or create a user
    user, _ = CustomUser.objects.get_or_create(username='testuser')

    # Get or create countries
    country1, _ = Country.objects.get_or_create(name='Benin', code='BJ')
    country2, _ = Country.objects.get_or_create(name='Togo', code='TG')

    # Get or create a project type
    project_type, _ = ProjectType.objects.get_or_create(name='Test Project Type')

    # Get or create a client
    client, _ = Client.objects.get_or_create(name='Test Client')

    # Create some projects
    project1, _ = Project.objects.get_or_create(
        name='Project Alpha',
        country=country1,
        defaults={
            'budget_alloue': 100000,
            'statut': 'IN_PROGRESS',
            'coordinator': user,
            'start_date': date(2023, 1, 15),
            'project_type': project_type,
            'client': client,
        }
    )
    project2, _ = Project.objects.get_or_create(
        name='Project Beta',
        country=country2,
        defaults={
            'budget_alloue': 200000,
            'statut': 'IN_PROGRESS',
            'coordinator': user,
            'start_date': date(2024, 3, 10),
            'project_type': project_type,
            'client': client,
        }
    )

    # Create some sites
    Site.objects.create(project=project1, name='Site A1', site_id_client='A1', start_date=date(2023, 2, 1), status='COMPLETED')
    Site.objects.create(project=project1, name='Site A2', site_id_client='A2', start_date=date(2023, 4, 5), status='COMPLETED')
    Site.objects.create(project=project2, name='Site B1', site_id_client='B1', start_date=date(2024, 5, 12), status='IN_PROGRESS')
    Site.objects.create(project=project2, name='Site B2', site_id_client='B2', start_date=date(2024, 6, 20), status='TO_DO')

    # Create some expenses
    Depense.objects.create(date=date(2023, 2, 15), montant=1500, description='Test Expense 1', projet_associe=project1)
    Depense.objects.create(date=date(2023, 4, 20), montant=2500, description='Test Expense 2', projet_associe=project1)
    Depense.objects.create(date=date(2024, 5, 25), montant=3500, description='Test Expense 3', projet_associe=project2)
    Depense.objects.create(date=date(2024, 6, 30), montant=4500, description='Test Expense 4', projet_associe=project2)

    # Create some revenues
    Revenu.objects.create(date=date(2023, 3, 1), montant=5000, projet_facture=project1)
    Revenu.objects.create(date=date(2023, 5, 1), montant=7000, projet_facture=project1)
    Revenu.objects.create(date=date(2024, 6, 1), montant=10000, projet_facture=project2)

    print("Test data added successfully!")

if __name__ == '__main__':
    add_test_data()
