from django.conf import settings


class ReferrerPolicyMiddleware:
    """Set a relaxed Referrer-Policy during local development.

    This middleware only sets the header when `DEBUG` is True to avoid
    changing production behaviour. Configure `DEV_REFERRER_POLICY` in
    settings to override the default.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.policy = getattr(settings, 'DEV_REFERRER_POLICY', 'no-referrer-when-downgrade')

    def __call__(self, request):
        response = self.get_response(request)
        if getattr(settings, 'DEBUG', False):
            response['Referrer-Policy'] = self.policy
        return response
