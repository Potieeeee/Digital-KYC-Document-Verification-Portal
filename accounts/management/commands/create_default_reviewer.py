from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group


class Command(BaseCommand):
    help = "Create a default reviewer user (local/dev)"

    def add_arguments(self, parser):
        parser.add_argument("--username", default="reviewer", help="Username for the reviewer")
        parser.add_argument("--email", default="reviewer@example.com", help="Email for the reviewer")
        parser.add_argument("--password", default="reviewerpassword", help="Password for the reviewer")

    def handle(self, *args, **options):
        User = get_user_model()
        username = options["username"]
        email = options["email"]
        password = options["password"]

        reviewer_group, _ = Group.objects.get_or_create(name="Reviewer")

        if User.objects.filter(username=username).exists():
            user = User.objects.get(username=username)
            if not user.groups.filter(name="Reviewer").exists():
                user.groups.add(reviewer_group)
                user.save()
                self.stdout.write(self.style.SUCCESS(f"Added existing user '{username}' to Reviewer group."))
            else:
                self.stdout.write(self.style.WARNING(f"User '{username}' already exists and is a Reviewer."))
            return

        user = User.objects.create_user(username=username, email=email, password=password)
        user.is_staff = True
        user.groups.add(reviewer_group)
        user.save()

        self.stdout.write(self.style.SUCCESS(f"Created reviewer user: {username}"))
