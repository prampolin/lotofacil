from django.conf import settings
from django.core.exceptions import RequestDataTooBig
from django.http import JsonResponse


class APIBodyLimitMiddleware:
    """Bound API payload bytes before DRF parses JSON or form data."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith("/api/v1/"):
            try:
                declared = int(request.META.get("CONTENT_LENGTH") or 0)
                if declared > settings.DATA_UPLOAD_MAX_MEMORY_SIZE:
                    raise RequestDataTooBig
                # A bounded read also protects against a missing/incorrect header.
                body = request.read(settings.DATA_UPLOAD_MAX_MEMORY_SIZE + 1)
                if len(body) > settings.DATA_UPLOAD_MAX_MEMORY_SIZE:
                    raise RequestDataTooBig
                from io import BytesIO

                request._body = body
                request._stream = BytesIO(body)
            except RequestDataTooBig:
                return JsonResponse({"detail": "Payload exceeds 64 KiB."}, status=413)
            except ValueError:
                return JsonResponse({"detail": "Invalid Content-Length."}, status=400)
        return self.get_response(request)
