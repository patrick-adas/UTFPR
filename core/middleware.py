class HtmxMiddleware:
    """Marca `request.htmx` como True quando a requisição vem do HTMX."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.htmx = request.headers.get("HX-Request") == "true"
        return self.get_response(request)
