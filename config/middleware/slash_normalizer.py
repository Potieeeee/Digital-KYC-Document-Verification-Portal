import re


class DuplicateSlashMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path_info = request.META.get("PATH_INFO", "")

        if "//" in path_info:
            normalized_path = re.sub(r"/{2,}", "/", path_info)
            request.META["PATH_INFO"] = normalized_path
            request.path_info = normalized_path

        return self.get_response(request)