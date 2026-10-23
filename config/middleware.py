class ResponseSecurityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.get_host()
        response = self.get_response(request)
        response.headers["Content-Security-Policy"] = (
            "default-src 'none'; script-src 'self'; style-src 'self'; "
            "img-src 'self'; font-src 'self'; connect-src 'self'; "
            "form-action 'self'; base-uri 'none'; frame-ancestors 'none'; object-src 'none'"
        )
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Cache-Control"] = "no-store, private"
        return response
