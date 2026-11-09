from django.contrib import admin

from .models import ComentarioTarefa, Tarefa


class ComentarioInline(admin.TabularInline):
    model = ComentarioTarefa
    extra = 0


@admin.register(Tarefa)
class TarefaAdmin(admin.ModelAdmin):
    list_display = ("titulo", "responsavel", "prazo", "prioridade", "status")
    list_filter = ("status", "prioridade", "responsavel")
    inlines = [ComentarioInline]
