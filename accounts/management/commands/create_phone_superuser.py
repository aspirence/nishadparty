from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import IntegrityError

User = get_user_model()

class Command(BaseCommand):
    help = 'Create a superuser with phone number'

    def add_arguments(self, parser):
        parser.add_argument('phone_number', type=str, help='Phone number for the superuser')
        parser.add_argument('--password', type=str, help='Password for the superuser')
        parser.add_argument('--first_name', type=str, help='First name for the superuser')
        parser.add_argument('--last_name', type=str, help='Last name for the superuser')

    def handle(self, *args, **options):
        phone_number = options['phone_number']
        password = options.get('password', 'admin123')  # Default password
        first_name = options.get('first_name', 'Admin')
        last_name = options.get('last_name', 'User')

        try:
            # Check if user already exists
            if User.objects.filter(phone_number=phone_number).exists():
                user = User.objects.get(phone_number=phone_number)
                user.is_superuser = True
                user.is_staff = True
                user.is_phone_verified = True
                user.user_type = 'ADMINISTRATOR'
                if password != 'admin123':  # Only set password if explicitly provided
                    user.set_password(password)
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(f'Updated existing user {phone_number} to superuser!')
                )
            else:
                # Create new superuser
                user = User.objects.create_superuser(
                    phone_number=phone_number,
                    password=password,
                    first_name=first_name,
                    last_name=last_name
                )
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully created superuser with phone: {phone_number}')
                )

            self.stdout.write(f'Phone: {user.phone_number}')
            self.stdout.write(f'Name: {user.get_full_name()}')
            self.stdout.write(f'Is Superuser: {user.is_superuser}')
            self.stdout.write(f'Is Staff: {user.is_staff}')

        except IntegrityError as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating superuser: {e}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Unexpected error: {e}')
            )