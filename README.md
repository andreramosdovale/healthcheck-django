# healthcheck-django

Monolito Django que substitui `healthcheck-api` (NestJS) e `healthcheck-app`
(Expo/React Native). Ver `../specs/` para a estratégia completa de migração e
os prompts de cada etapa.

**Projeto local, uso pessoal**: banco **SQLite** (`db.sqlite3`, arquivo
único, sem Docker/Postgres), sem deploy configurado. Tabelas 100% no padrão
Django (`accounts_user`, `measurements_measurement`, etc. — sem prefixos
customizados).

Status: **Prompts 1 a 5 concluídos**, simplificado depois para SQLite local
(sem Postgres, sem Docker, sem migração de dados do backend antigo — este
projeto não compartilha mais banco com `healthcheck-api`).

- Auth: model `User` customizado (`accounts.User`), login por email OU
  nickname (`accounts/backends.py`), senha complexa
  (`accounts/validators.py`), grupos RBAC `user`/`admin`/`professional`.
- Medições: model `Measurement`, cálculo de %gordura (Pollock 7-dobras /
  Navy), massa magra/gorda, WHR — `measurements/services.py`.
- Evolução: gráficos (Chart.js + HTMX) e séries/comparação/tendência/delta —
  `evolution/services.py`.
- **UI**: [shadcn_django](https://github.com/SarthakJariwala/shadcn-django)
  (componentes shadcn/ui portados para Django via
  [django-cotton](https://django-cotton.com)) + Tailwind CSS v4 rodando via
  [django-tailwind-cli](https://django-tailwind-cli.readthedocs.io) (binário
  standalone, **sem Node.js**). Paleta reaproveitada do app mobile
  (`healthcheck-app`, emerald/gray) — ver `src/styles/source.css`.

## Setup

```bash
cd healthcheck-django
python -m venv .venv
./.venv/Scripts/activate   # Windows
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py tailwind build   # gera static/css/tailwind.css (gitignored)
python manage.py createsuperuser
python manage.py runserver
```

Durante o desenvolvimento, se for mexer nos templates/estilos, rode em outro
terminal para recompilar o CSS automaticamente ao salvar:
```bash
python manage.py tailwind watch
```

### UI / componentes (shadcn_django)

Os componentes já usados (`button`, `card`, `input`, `label`, `badge`,
`alert`, `table`, `separator`) ficam em `templates/cotton/` — são arquivos
`.html` normais, editáveis à vontade (filosofia shadcn: você é dono do
código, não é uma dependência de pacote). Para adicionar mais componentes
(ex.: `dialog`, `select`, `tabs`):
```bash
uvx shadcn_django add dialog
```
Uso nos templates: `<c-button variant="outline">Cancelar</c-button>`,
`<c-card><c-card.header>...</c-card.header></c-card>` etc. Os campos de
formulário (`<input>`, `<select>`, checkbox) recebem as classes do design
system automaticamente via `TailwindFormMixin`
(`config/tailwind_forms.py`) — não precisa envolver cada campo manualmente.

Abra `http://127.0.0.1:8000/accounts/login/` (ou `/accounts/register/`) e
`http://127.0.0.1:8000/admin/`.

O banco é o arquivo `db.sqlite3` na raiz do projeto (gitignored). Para
resetar tudo, basta apagar esse arquivo e rodar `migrate` de novo.

## Estrutura

```
config/settings/{base,dev,prod}.py
config/tailwind_forms.py       # aplica classes Tailwind aos forms
accounts/       # auth + users
measurements/   # medições e cálculo de %gordura
evolution/      # gráficos de evolução
templates/base.html
templates/cotton/               # componentes shadcn_django (button, card, input, ...)
src/styles/source.css           # tema (cores, radius) do Tailwind/shadcn
```
