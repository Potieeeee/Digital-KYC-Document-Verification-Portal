from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model


class EmailOrUsernameBackend(ModelBackend):
    """Authenticate users by username or email address."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        identifier = username or kwargs.get(UserModel.USERNAME_FIELD)

        if not identifier or password is None:
            return None

        username_matches = UserModel.objects.filter(username__iexact=identifier).order_by("id")
        email_matches = UserModel.objects.filter(email__iexact=identifier).order_by("id")

        candidates = []
        seen_ids = set()

        for candidate in username_matches:
            if candidate.id not in seen_ids:
                candidates.append(candidate)
                seen_ids.add(candidate.id)

        for candidate in email_matches:
            if candidate.id not in seen_ids:
                candidates.append(candidate)
                seen_ids.add(candidate.id)

        for candidate in candidates:
            if candidate.check_password(password) and self.user_can_authenticate(candidate):
                return candidate

        return None