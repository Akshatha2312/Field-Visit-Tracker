from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = "Create admin user if it doesn't exist"

    def handle(self, *args, **kwargs):
        username = "admin"
        email = "admin@example.com"
        password = "Admin@123"

        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING("Admin user already exists"))
        else:
            User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
            )
            self.stdout.write(self.style.SUCCESS("Admin user created successfully"))