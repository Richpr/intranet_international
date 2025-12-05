from django.core.management.base import BaseCommand
from users.models import Role

class Command(BaseCommand):
    help = 'Creates default roles (Technician, Rigger) if they do not exist.'

    def handle(self, *args, **options):
        roles_to_create = ['Technician', 'Rigger']
        created_count = 0

        for role_name in roles_to_create:
            role, created = Role.objects.get_or_create(name=role_name)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Successfully created role: {role_name}'))
                created_count += 1
            else:
                self.stdout.write(self.style.WARNING(f'Role "{role_name}" already exists.'))
        
        if created_count > 0:
            self.stdout.write(self.style.SUCCESS(f'Finished creating {created_count} new role(s).'))
        else:
            self.stdout.write(self.style.SUCCESS('All default roles already exist. No new roles were created.'))
