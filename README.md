# Rede Farmácia

Rede interna de comunicação e gestão da equipe de uma farmácia, no estilo de uma rede social. Funciona no navegador do computador e do celular e pode ser **instalada como app (PWA)**.

## O que cada um pode fazer

| Funcionalidade | Proprietário | Colaborador |
|---|---|---|
| **Feed**: publicar recados gerais, com foto, curtir e comentar | ✅ (e fixar/moderar posts) | ✅ |
| **Recados oficiais**, gerais ou privados para pessoas escolhidas, com confirmação de leitura | cria e vê quem leu | lê (a leitura é confirmada ao abrir) |
| **Tarefas** com responsável, prazo, prioridade, status e comentários | atribui e acompanha a equipe toda | vê as suas, muda o status e comenta |
| **Metas mensais** da farmácia e individuais, com barra de progresso | cria, lança o progresso e copia do mês anterior | acompanha as suas e as da farmácia e lança nas suas individuais* |
| **Mensagens privadas** entre colegas (atualizam a cada 5 s) | ✅ | ✅ |
| **Equipe**: criar contas, redefinir senha, desativar | ✅ | — |

\* Configurável com a variável `COLABORADOR_PODE_LANCAR` (padrão: `true`).

Não existe cadastro público: o proprietário cria cada conta com uma senha inicial, e o colaborador precisa trocá-la no primeiro acesso. Os badges de não lidos (recados, tarefas e mensagens) se atualizam sozinhos a cada 30 s.

## Rodando localmente

Requisito: Python 3.11+.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo      # dados de exemplo (opcional)
python manage.py runserver
```

Acesse http://127.0.0.1:8000. Com os dados de exemplo, a senha de todos é `farmacia123`:
- `dono` (proprietária, também acessa `/admin/`);
- `ana`, `bruno` e `carla` (colaboradores).

Para começar com o banco vazio, crie só a conta do proprietário:

```bash
python manage.py createsuperuser
python manage.py shell -c "from accounts.models import User; User.objects.filter(is_superuser=True).update(papel='PROPRIETARIO')"
```

## Testes

```bash
python manage.py test
```

## Publicando (produção)

Variáveis de ambiente:

| Variável | Exemplo |
|---|---|
| `DJANGO_DEBUG` | `0` |
| `DJANGO_SECRET_KEY` | uma chave longa e aleatória |
| `DJANGO_ALLOWED_HOSTS` | `rede.minhafarmacia.com.br` |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | `https://rede.minhafarmacia.com.br` |
| `DATABASE_URL` | `postgres://usuario:senha@host:5432/farmacia` (sem ela, usa SQLite) |
| `DJANGO_MEDIA_ROOT` | pasta persistente para as fotos enviadas |

```bash
python manage.py migrate
python manage.py collectstatic --noinput
gunicorn farmacia.wsgi --bind 0.0.0.0:8000
```

- Os arquivos estáticos são servidos pelo WhiteNoise.
- As fotos enviadas (`/media/`) só são entregues a usuários logados.
- O PWA (instalar na tela inicial) exige **HTTPS** em produção.
- Para checar a saúde da aplicação, use `GET /healthz`.

## Estrutura

```
farmacia/   configurações e URLs
core/       início (dashboard), PWA (manifest, service worker), permissões, utilitários
accounts/   usuário (papel, cargo, foto), login, troca de senha, gestão da equipe
feed/       posts, comentários e curtidas
recados/    recados gerais/privados + confirmação de leitura
tarefas/    tarefas atribuídas
metas/      metas mensais + lançamentos de progresso
mensagens/  conversas privadas com atualização por polling (HTMX)
templates/  HTML (Django templates + HTMX)
static/     CSS, JS, HTMX e ícones
```

## Próximos passos sugeridos

- Notificações push no celular (Web Push), para avisar de mensagens e recados novos.
- Conversas em grupo.
- Integração com o sistema de vendas (PDV/ERP), para lançar o progresso das metas automaticamente.
