from django.contrib import admin

from .models import Lancamento, MetaMensal


class LancamentoInline(admin.TabularInline):
    model = Lancamento
    extra = 0


@admin.register(MetaMensal)
class MetaAdmin(admin.ModelAdmin):
    list_display = ("titulo", "mes", "escopo", "responsavel", "valor_alvo", "unidade")
    list_filter = ("escopo", "mes")
    inlines = [LancamentoInline]
