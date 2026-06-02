from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group

class Command(BaseCommand):
    help = "Create default user roles"

    def handle(self, *args, **kwargs):
        roles = ["Client", "Reviewer", "Manager", "Admin", "ThirdPartyAPI"]

        for role in roles:
            Group.objects.get_or_create(name=role)
            self.stdout.write(self.style.SUCCESS(f"Role created: {role}"))