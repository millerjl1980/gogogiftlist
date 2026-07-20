class DevelopmentCorsMiddleware:
    """Allow the Vite development server to use Django's session API."""

    allowed_origins = {"http://localhost:3000", "http://127.0.0.1:3000"}

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        origin = request.headers.get("Origin")
        if request.method == "OPTIONS" and origin in self.allowed_origins:
            response = self._preflight_response()
        else:
            response = self.get_response(request)
        if origin in self.allowed_origins:
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
