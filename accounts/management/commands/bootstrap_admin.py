import os

from django.contrib.auth import get_user_model, password_validation
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Create the initial admin from ADMIN_USERNAME, ADMIN_EMAIL, and ADMIN_PASSWORD.'

    def handle(self, *args, **options):
        username = os.environ.get('ADMIN_USERNAME', '').strip()
        email = os.environ.get('ADMIN_EMAIL', '').strip()
        password = os.environ.get('ADMIN_PASSWORD', '')

        if not username or not email or not password:
            raise CommandError(
                'Set ADMIN_USERNAME, ADMIN_EMAIL, and ADMIN_PASSWORD to bootstrap an admin.'
            )

        User = get_user_model()
        existing_user = User._default_manager.filter(
            username__iexact=username
        ).first()
        if existing_user:
            if existing_user.is_staff and existing_user.is_superuser:
                self.stdout.write('Admin account already exists; no changes made.')
                return
            raise CommandError(
                f'Username "{username}" already belongs to a non-admin account. '
                'Choose a different ADMIN_USERNAME.'
            )

        candidate = User(username=username, email=email)
        try:
            password_validation.validate_password(password, user=candidate)
        except ValidationError as exc:
            raise CommandError(f'ADMIN_PASSWORD is not valid: {exc}') from exc

        User._default_manager.create_superuser(
            username=username,
            email=email,
            password=password,
        )
        self.stdout.write(self.style.SUCCESS(f'Created admin account "{username}".'))
