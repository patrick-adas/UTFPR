from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def proprietario_required(view):
    """Permite acesso apenas a usuários logados com papel de proprietário."""

    @login_required
    @wraps(view)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_proprietario:
            raise PermissionDenied("Apenas o proprietário pode acessar esta página.")
        return view(request, *args, **kwargs)

    return _wrapped
