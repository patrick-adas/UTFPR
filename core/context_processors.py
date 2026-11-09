from django.conf import settings


def calcular_contadores(user):
    from mensagens.models import total_nao_lidas
    from recados.models import Recado
    from tarefas.models import Tarefa

    return {
        "mensagens": total_nao_lidas(user),
        "recados": Recado.objects.nao_lidos_por(user).count(),
        "tarefas": Tarefa.objects.filter(responsavel=user).abertas().count(),
    }


def contadores(request):
    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated or request.path.startswith("/admin/"):
        return {}
    return {
        "contadores": calcular_contadores(user),
        "polling_contadores": settings.POLLING_CONTADORES_SEGUNDOS,
    }
