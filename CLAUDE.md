# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

`healthcheck-django` is a Django monolith for tracking personal body
composition over time: measurements (weight, skinfolds, circumferences),
derived body-fat calculations, and evolution/progress charts.

This is a **local-only, single-user project**: SQLite (`db.sqlite3`), no
Docker, no Postgres, no deploy config. Don't reintroduce those unless
explicitly asked.

## Commands

```bash
# activate the venv first (Windows)
.venv\Scripts\activate.bat        # cmd
./.venv/Scripts/Activate.ps1      # powershell

python manage.py runserver
python manage.py migrate
python manage.py makemigrations <app>
python manage.py createsuperuser
python manage.py check

# Tailwind CSS (standalone CLI, no Node.js) — rebuild after touching any
# template or `src/styles/source.css`, since `static/css/tailwind.css` is
# gitignored and NOT rebuilt automatically by runserver:
python manage.py tailwind build
python manage.py tailwind build --force   # force rebuild even if "up to date"
python manage.py tailwind watch           # auto-rebuild on save, run in a second terminal

# Add a shadcn_django UI component (creates templates/cotton/<name>/*.html)
uvx shadcn_django add <component>
uvx shadcn_django list
```

There is no test suite yet (`tests.py` in each app is the default empty
stub) and no linter/formatter configured — don't assume `pytest`, `ruff`, or
`black` are available.

Manual verification pattern used throughout this project's history (no
Docker/Postgres needed): spin up a throwaway `config/settings/_smoketest.py`
importing from `base` and pointing `DATABASES` at a temp SQLite file, run
`migrate`, then exercise logic via `manage.py shell -c "..."` or
`django.test.Client()` with `force_login`. Delete the temp settings file and
SQLite file when done.

## Architecture

**Three Django apps, one per business domain**, each owning its models,
`services.py` (business logic / calculations kept out of views), forms,
views, urls, and app-local templates:

- `accounts` — custom `User` model (`AUTH_USER_MODEL = "accounts.User"`,
  UUID pk, email/nickname both usable as login identifier via
  `accounts/backends.py:EmailOrNicknameBackend`). Password complexity rule
  lives in `accounts/validators.py`. RBAC groups (`user`/`admin`/`professional`)
  are created by the data migration `accounts/migrations/0002_rbac_groups.py`,
  not by fixtures.
- `measurements` — `Measurement` model (weight, 7 skinfolds, 13+
  circumferences). `measurements/services.py` computes body-fat % from
  Pollock 7-fold (preferred, needs all 7 skinfolds + age + sex) or Navy
  (fallback, needs neck/waist/height, +hip for women), plus lean/fat mass and
  waist-hip ratio with WHO risk classification. Skinfolds are all-or-nothing
  (`SkinfoldsIncompleteError`) — enforced in `MeasurementForm.clean()`.
  Calculated fields are **never** user input; they're always derived by
  `apply_calculations()` in the view right before `save()`.
- `evolution` — no models of its own; `evolution/services.py` reads
  `measurements` and computes time-series (`get_summary`), a two-point diff
  (`get_compare`), trend classification (`get_latest`, producing a semantic
  `trend_code` such as `excellent_progress`/`good_progress`/`fat_increased`/
  `stable_results` or a weight-based fallback), and per-field direction vs.
  the previous measurement (`get_delta`, with fixed stability thresholds and
  a weighted `composition_balance` score). Charts are
  Chart.js, re-rendered via an HTMX-swapped partial
  (`evolution/templates/evolution/_charts.html`) — see `_parse_range()` in
  `evolution/views.py` for the `range` query param format (`weeks-N`,
  `count-N`, or `all`).

**Cross-cutting:**

- `config/tailwind_forms.py` — `TailwindFormMixin`, mixed into every
  `forms.Form`/`ModelForm` to auto-apply the design-system input/checkbox
  classes to widgets. Add it to any new form instead of styling fields by
  hand in templates.
- UI is [shadcn_django](https://github.com/SarthakJariwala/shadcn-django)
  (shadcn/ui ported to Django via `django-cotton`) + Tailwind v4 via
  `django-tailwind-cli` (standalone binary, no Node). Reusable components
  live in `templates/cotton/<name>/` as plain, directly-editable `.html`
  files (`<c-button>`, `<c-card>`, `<c-card.header>`, etc. — not a package
  dependency). Theme tokens (colors, radius) are in `src/styles/source.css`
  (emerald primary, gray neutrals).
- `config/settings/` is split into `base.py` / `dev.py` / `prod.py`.
  `manage.py` defaults to `dev`; `wsgi.py`/`asgi.py` default to `prod`
  (`prod.py` hard-fails if `ALLOWED_HOSTS` is empty or `SECRET_KEY` looks
  like the Django-generated placeholder — expected to stay unused for now
  since this project has no deploy target).
- All ownership checks follow the same pattern: `get_object_or_404(Model, pk=pk, user=request.user)` — every cross-app query in `measurements`/`evolution` filters by
  the logged-in user; there is no cross-user access anywhere.
