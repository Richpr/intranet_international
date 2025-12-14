import logging
from django.core.management.base import BaseCommand
from django.db import transaction
from users.models import CustomUser

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Generates employee IDs for existing users based on hire_date, following the AAMMNN format.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting employee ID generation/regeneration for all users with a hire date...'))

        # Filter for all users with a hire_date, as per the requirement to apply to all employees,
        # including old ones, to ensure they conform to the new format.
        users_to_update = CustomUser.objects.filter(
            hire_date__isnull=False
        ).order_by('hire_date', 'id') # Order for consistent 'NN' generation

        total_users = users_to_update.count()
        self.stdout.write(f'Found {total_users} users requiring an employee ID.')

        if not users_to_update:
            self.stdout.write(self.style.WARNING('No users found requiring an employee ID. Exiting.'))
            return

        updated_count = 0
        with transaction.atomic():
            for user in users_to_update:
                try:
                    # Call the new _generate_employee_id method
                    user.employee_id = user._generate_employee_id()
                    if user.employee_id:
                        user.save(update_fields=['employee_id'])
                        updated_count += 1
                        self.stdout.write(f'Successfully generated ID {user.employee_id} for user {user.username or user.email}.')
                    else:
                        self.stdout.write(self.style.WARNING(f'Skipping user {user.username or user.email} (ID: {user.pk}) as employee ID could not be generated (missing hire_date?).'))

                except Exception as e:
                    self.stderr.write(self.style.ERROR(f'Error generating ID for user {user.username or user.email} (ID: {user.pk}): {e}'))
                    # Depending on policy, you might want to re-raise or continue

        self.stdout.write(self.style.SUCCESS(f'Finished generating employee IDs. {updated_count} out of {total_users} users updated successfully.'))

        if updated_count != total_users:
            self.stdout.write(self.style.WARNING('Some users could not be updated. Please check the logs for errors.'))
