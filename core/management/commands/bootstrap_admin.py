import os

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Create the first dashboard administrator from environment variables, if configured."

    def handle(self, *args, **options):
        username = os.environ.get("DJANGO_SUPERUSER_USERNAME", "").strip()
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "").strip()
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "")
        if not all((username, email, password)):
            self.stdout.write("Admin bootstrap skipped: administrator environment values are not all configured.")
            return

        User = get_user_model()
        existing = User.objects.filter(**{User.USERNAME_FIELD: username}).first()
        if existing:
            if not existing.is_staff or not existing.is_superuser:
                raise CommandError("The configured admin username already belongs to a non-admin account.")
            self.stdout.write("Dashboard administrator already exists.")
            return

        user = User(**{User.USERNAME_FIELD: username, "email": email})
        try:
            validate_password(password, user)
        except Exception as exc:
            raise CommandError("The configured administrator password does not pass Django's password checks.") from exc
        User.objects.create_superuser(username=username, email=email, password=password)
        self.stdout.write(self.style.SUCCESS("Dashboard administrator created."))
