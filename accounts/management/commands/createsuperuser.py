from django.contrib.auth.management.commands.createsuperuser import Command as BaseCommand
from django.core.management import CommandError
from django.contrib.auth import get_user_model
from django.db import IntegrityError

User = get_user_model()

class Command(BaseCommand):
    help = 'Create a superuser with phone number authentication'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove username from required fields since we use phone_number
        self.UserModel = User
        self.username_field = self.UserModel._meta.get_field('phone_number')

    def add_arguments(self, parser):
        parser.add_argument(
            '--phone_number',
            help='Phone number for the superuser',
        )
        parser.add_argument(
            '--first_name',
            help='First name for the superuser',
        )
        parser.add_argument(
            '--last_name',
            help='Last name for the superuser',
        )
        parser.add_argument(
            '--noinput', '--no-input',
            action='store_false', dest='interactive', default=True,
            help='Don\'t prompt the user for input',
        )

    def handle(self, *args, **options):
        phone_number = options.get('phone_number')
        first_name = options.get('first_name')
        last_name = options.get('last_name')
        interactive = options.get('interactive', True)

        if interactive:
            # Interactive mode - prompt for inputs
            if not phone_number:
                phone_number = input('Phone number: ')

            if not first_name:
                first_name = input('First name (optional): ') or 'Admin'

            if not last_name:
                last_name = input('Last name (optional): ') or 'User'

            password = None
            while not password:
                password = input('Password: ')
                if not password:
                    self.stderr.write('Error: Password cannot be blank.')
                    continue

            # Confirm password
            password2 = input('Password (again): ')
            if password != password2:
                self.stderr.write('Error: Your passwords didn\'t match.')
                return
        else:
            # Non-interactive mode
            if not phone_number:
                raise CommandError('You must specify --phone-number in non-interactive mode')
            first_name = first_name or 'Admin'
            last_name = last_name or 'User'
            password = 'admin123'  # Default password for non-interactive

        try:
            # Check if user already exists
            if User.objects.filter(phone_number=phone_number).exists():
                user = User.objects.get(phone_number=phone_number)
                user.is_superuser = True
                user.is_staff = True
                user.is_phone_verified = True
                user.user_type = 'ADMINISTRATOR'
                if first_name:
                    user.first_name = first_name
                if last_name:
                    user.last_name = last_name
                if password and password != 'admin123':  # Only set password if explicitly provided
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
                    self.style.SUCCESS(f'Superuser created successfully!')
                )

            # Display user info
            self.stdout.write(f'Phone: {user.phone_number}')
            self.stdout.write(f'Name: {user.get_full_name()}')
            self.stdout.write(f'Is Superuser: {user.is_superuser}')
            self.stdout.write(f'Is Staff: {user.is_staff}')

        except IntegrityError as e:
            raise CommandError(f'Error creating superuser: {e}')
        except Exception as e:
            raise CommandError(f'Unexpected error: {e}')