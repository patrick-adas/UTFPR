from django.contrib import admin

from .models import Conversa, Mensagem


class MensagemInline(admin.TabularInline):
    model = Mensagem
    extra = 0


@admin.register(Conversa)
class ConversaAdmin(admin.ModelAdmin):
    list_display = ("__str__", "atualizada_em")
    inlines = [MensagemInline]
