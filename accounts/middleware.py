from django.shortcuts import redirect
from django.urls import reverse


class TrocaSenhaObrigatoriaMiddleware:
    """Redireciona para a troca de senha quando a conta foi criada/redefinida pelo proprietário."""

    CAMINHOS_LIVRES = ("/static/", "/media/", "/sw.js", "/manifest.webmanifest", "/offline/", "/healthz")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated and user.deve_trocar_senha:
            permitidos = {reverse("accounts:trocar_senha"), reverse("accounts:logout")}
            if request.path not in permitidos and not request.path.startswith(self.CAMINHOS_LIVRES):
                return redirect("accounts:trocar_senha")
        return self.get_response(request)
