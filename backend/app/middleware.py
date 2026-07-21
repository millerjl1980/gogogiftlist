class DevelopmentCorsMiddleware:
    """Allow explicitly configured browser origins to use the session API."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        from django.conf import settings

        allowed_origins = set(settings.CSRF_TRUSTED_ORIGINS)
        origin = request.headers.get("Origin")
        if request.method == "OPTIONS" and origin in allowed_origins:
            response = self._preflight_response()
        else:
            response = self.get_response(request)
        if origin in allowed_origins:
            response["Access-Control-Allow-Origin"] = origin
            response["Access-Control-Allow-Credentials"] = "true"
            response["Access-Control-Allow-Headers"] = "Content-Type, X-CSRFToken"
            response["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
            response["Vary"] = "Origin"
        return response

    @staticmethod
    def _preflight_response():
        from django.http import HttpResponse

        return HttpResponse(status=204)
