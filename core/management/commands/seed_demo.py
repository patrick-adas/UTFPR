import datetime
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from accounts.models import User
from core.utils import inicio_do_mes
from feed.models import Comentario, Curtida, Post
from mensagens.models import Conversa, Mensagem
from metas.models import Lancamento, MetaMensal
from recados.models import Leitura, Recado
from tarefas.models import Tarefa

SENHA_DEMO = "farmacia123"


class Command(BaseCommand):
    help = "Cria dados de demonstração (proprietário, colaboradores, posts, recados, tarefas, metas e mensagens)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--apagar", action="store_true", help="Apaga TODOS os dados existentes antes de criar a demonstração."
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if User.objects.exists():
            if not options["apagar"]:
                raise CommandError("Já existem usuários no banco. Use --apagar para recriar os dados de demonstração.")
            for modelo in (Mensagem, Conversa, Lancamento, MetaMensal, Tarefa, Leitura, Recado, Curtida, Comentario, Post, User):
                modelo.objects.all().delete()

        def criar(username, nome, sobrenome, papel, cargo):
            u = User(username=username, first_name=nome, last_name=sobrenome, papel=papel, cargo=cargo)
            u.set_password(SENHA_DEMO)
            u.save()
            return u

        dono = criar("dono", "Patrícia", "Andrade", User.Papel.PROPRIETARIO, "Proprietária")
        dono.is_staff = dono.is_superuser = True
        dono.save()
        ana = criar("ana", "Ana", "Souza", User.Papel.COLABORADOR, "Farmacêutica")
        bruno = criar("bruno", "Bruno", "Lima", User.Papel.COLABORADOR, "Balconista")
        carla = criar("carla", "Carla", "Mendes", User.Papel.COLABORADOR, "Caixa")

        agora = timezone.now()
        hoje = timezone.localdate()
        mes = inicio_do_mes()

        # Feed
        p1 = Post.objects.create(autor=dono, texto="Bom dia, equipe! Esta é a nossa nova rede interna. Usem o feed para avisos do dia a dia. 💚", fixado=True)
        p2 = Post.objects.create(autor=ana, texto="Chegou a reposição de dipirona e vitamina C. Já está tudo no estoque da prateleira 3.")
        p3 = Post.objects.create(autor=bruno, texto="Alguém pode cobrir meu horário de almoço amanhã às 12h? Tenho consulta médica.")
        Comentario.objects.create(post=p3, autor=carla, texto="Eu cubro, Bruno!")
        Comentario.objects.create(post=p2, autor=dono, texto="Obrigada, Ana!")
        for post, quem in ((p1, ana), (p1, bruno), (p1, carla), (p2, dono), (p3, carla)):
            Curtida.objects.create(post=post, usuario=quem)

        # Recados
        Recado.objects.create(
            autor=dono, titulo="Inventário no sábado",
            texto="No sábado faremos o inventário a partir das 14h. Todos precisam estar presentes até as 18h.",
            importante=True,
        )
        Recado.objects.create(
            autor=dono, titulo="Novo procedimento de receitas controladas",
            texto="A partir de segunda, toda receita de controlado deve ser conferida por dois colaboradores antes da dispensação.",
        )
        privado = Recado.objects.create(
            autor=dono, titulo="Parabéns pelo atendimento!", tipo=Recado.Tipo.PRIVADO,
            texto="Ana, recebemos um elogio de cliente sobre o seu atendimento ontem. Muito obrigada!",
        )
        privado.destinatarios.add(ana)

        # Tarefas
        Tarefa.objects.create(titulo="Conferir validade dos produtos da gôndola 2", responsavel=bruno, criada_por=dono,
                              prazo=hoje + datetime.timedelta(days=2), prioridade=Tarefa.Prioridade.ALTA)
        Tarefa.objects.create(titulo="Organizar vitrine de dermocosméticos", responsavel=carla, criada_por=dono,
                              prazo=hoje + datetime.timedelta(days=5))
        Tarefa.objects.create(titulo="Enviar pedido de reposição ao distribuidor", responsavel=ana, criada_por=dono,
                              prazo=hoje - datetime.timedelta(days=1), status=Tarefa.Status.EM_ANDAMENTO)
        t = Tarefa.objects.create(titulo="Atualizar cadastro de clientes do programa de fidelidade", responsavel=ana,
                                  criada_por=dono, prioridade=Tarefa.Prioridade.BAIXA)
        t.mudar_status(Tarefa.Status.CONCLUIDA)

        # Metas
        def meta(titulo, alvo, unidade, responsavel=None, lancamentos=()):
            m = MetaMensal.objects.create(
                titulo=titulo, mes=mes, valor_alvo=Decimal(alvo), unidade=unidade, criada_por=dono,
                escopo=MetaMensal.Escopo.INDIVIDUAL if responsavel else MetaMensal.Escopo.FARMACIA,
                responsavel=responsavel,
            )
            for i, valor in enumerate(lancamentos):
                Lancamento.objects.create(meta=m, valor=Decimal(valor), lancado_por=responsavel or dono,
                                          data=max(mes, hoje - datetime.timedelta(days=len(lancamentos) - i)))
            return m

        meta("Faturamento do mês", "120000", "R$", lancamentos=("18500", "22300", "15750"))
        meta("Clientes no programa de fidelidade", "150", "cadastros", lancamentos=("40", "35"))
        meta("Vendas de dermocosméticos", "8000", "R$", responsavel=carla, lancamentos=("2100", "1850"))
        meta("Atendimentos farmacêuticos", "60", "atendimentos", responsavel=ana, lancamentos=("22", "19"))
        meta("Vendas de genéricos", "300", "unidades", responsavel=bruno, lancamentos=("80",))

        # Mensagens
        conversa = Conversa.obter_ou_criar(ana, bruno)
        Mensagem.objects.create(conversa=conversa, autor=bruno, texto="Ana, você sabe onde ficou o termolábil que chegou hoje?")
        Mensagem.objects.create(conversa=conversa, autor=ana, texto="Está na geladeira de baixo, já conferi a temperatura.")
        conversa.marcar_lida(ana)
        conversa2 = Conversa.obter_ou_criar(dono, carla)
        Mensagem.objects.create(conversa=conversa2, autor=dono, texto="Carla, pode fechar o caixa às 19h hoje?")

        self.stdout.write(self.style.SUCCESS(
            f"Dados de demonstração criados em {agora:%d/%m/%Y %H:%M}.\n"
            f"Logins (senha '{SENHA_DEMO}'): dono (proprietária), ana, bruno, carla."
        ))
