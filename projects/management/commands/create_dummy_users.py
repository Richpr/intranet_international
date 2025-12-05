import datetime
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
import random

CustomUser = get_user_model()

class Command(BaseCommand):
    help = 'Creates dummy CustomUser instances with hire_date for testing employee ID generation.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--num_users',
            type=int,
            default=5,
            help='The number of dummy users to create.',
        )

    def handle(self, *args, **options):
        num_users = options['num_users']
        self.stdout.write(f'Creating {num_users} dummy users...')

        today = timezone.now().date()
        
        # Create users with hire dates spanning a few months/years
        for i in range(num_users):
            year = random.choice([today.year - 1, today.year]) # last year or current year
            month = random.randint(1, 12)
            day = random.randint(1, 28) # To avoid month-end issues
            hire_date = datetime.date(year, month, day)

            username = f'dummyuser_{i}_{random.randint(1000, 9999)}'
            email = f'{username}@example.com'
            password = 'password123'
            first_name = f'Dummy{i}'
            last_name = f'User{i}'

            try:
                user = CustomUser.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    hire_date=hire_date # This will trigger the save method's ID generation
                )
                self.stdout.write(self.style.SUCCESS(f'Successfully created dummy user: {user.username} with hire_date {user.hire_date}. Employee ID: {user.employee_id}'))
            except Exception as e:
                self.stderr.write(self.style.ERROR(f'Error creating dummy user {username}: {e}'))

        self.stdout.write(self.style.SUCCESS(f'Finished creating {num_users} dummy users.'))
