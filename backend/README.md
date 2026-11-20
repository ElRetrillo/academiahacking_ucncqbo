# EclipSec CTF - Backend API Service

Servicio backend asincrono construido con **FastAPI**, **SQLAlchemy (Async)**, **Alembic** y **PostgreSQL / SQLite**, disenado para ejecutarse en **Railway** e integrarse de forma segura con el portal web **EclipSec** (`eclipsec.cl`) y el cliente **eclipsecCLI**.

---

## Capacidades Principales

1. **Autenticacion, Sesiones Web y Telemetria**:
   - Registro y autenticacion via `bcrypt` (validacion UTF-8 hasta 72 bytes) y JWT (`HS256`) con `jti` revocable en `revoked_tokens`.
   - Sesion web segura mediante cookies `HttpOnly` + doble validacion CSRF (`X-CSRF-Token`) y tokens acotados para `eclipsecCLI`.
   - Registro de `nationality`, puntaje acumulado (`score`), fecha de ingreso (`created_at`) y ultima conexion (`last_connected_at`).
2. **Gestion de Retos, Instancias CLI y Validacion de Flags**:
   - Catalogo filtrable por categoria y dificultad con resolucion dinamica de `target_url` via `CHALLENGES_BASE_URL`.
   - Verificacion en tiempo constante contra resumenes `HMAC-SHA256`, registro de envios hasheados e incrementos atomicos anti-carrera protegidos por `uq_user_challenge_solve`.
   - Registro idempotente de sesiones locales (`/start`, `/stop`) con metadatos de repositorio (`repository`, `path`, `version`) para `eclipsecCLI`.
3. **Leaderboard Unificado y Perfiles**:
   - Ranking global SQL ordenado por `score DESC`, `last_solve_at ASC NULLS LAST`, `created_at ASC`, `id ASC`, compartido de manera consistente entre leaderboard, perfil y adaptador academy.
   - Perfiles publicos segregados (`UserPublicProfileDetail`) sin exposicion de PII.
4. **Administracion RBAC, Arquitectura por Capas y Migraciones**:
   - Arquitectura `Routers -> Servicios -> Repositorios (Protocol)` con inyeccion de dependencias.
   - CRUD completo de retos y administracion de usuarios con proteccion contra auto-bloqueo de administradores (`/api/v1/admin/*`).
   - Migraciones versionadas mediante **Alembic** y adaptador de compatibilidad en `POST /api/ctf-academy`.

Para revisar la referencia completa de contratos, payloads y arquitectura, consulta [Referencia de la API](../docs/API_REFERENCE.md), [Arquitectura del Sistema](../docs/ARCHITECTURE.md) y la [Auditoria Tecnica](../docs/PROJECT_AUDIT.md).

---

## Resumen de Endpoints

| Grupo | Prefijo | Endpoints Principales |
|---|---|---|
| Salud | `/` | `GET /`, `GET /health` |
| Autenticacion | `/api/v1/auth` | `POST /register`, `POST /login`, `POST /session/login`, `POST /session/logout`, `POST /logout`, `GET /me`, `PUT /me` |
| Retos e Instancias | `/api/v1/challenges` | `GET /`, `GET /recent`, `GET /categories`, `GET /{id_or_slug}`, `POST /{id_or_slug}/submit`, `POST /{id_or_slug}/start`, `POST /{id_or_slug}/stop` |
| Leaderboard | `/api/v1/leaderboard` | `GET /`, `GET /countries` |
| Usuarios | `/api/v1/users` | `GET /{username}/profile` |
| Administracion | `/api/v1/admin` | `GET/POST /challenges`, `PUT/DELETE /challenges/{id}`, `GET /users`, `PUT /users/{id}` |
| Adaptador Legacy | `/api/ctf-academy` | `POST /api/ctf-academy` |

---

## Ejecucion Local

### Requisitos
- Python 3.11+
- `pip` y `venv`

### Configuracion en Windows (PowerShell)

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
alembic upgrade head
python seed.py
uvicorn app.main:app --reload --port 8000
```

### Configuracion en Linux / macOS

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
python seed.py
uvicorn app.main:app --reload --port 8000
```

Documentacion interactiva disponible en `http://localhost:8000/docs`.

El backend resuelve automaticamente sus rutas de `.env`, `ctf.db`, `alembic.ini` y `seed.py` con `pathlib.Path`, por lo que tambien funciona ejecutandolo desde la raiz del repositorio en Windows, Linux o macOS:

```bash
alembic -c backend/alembic.ini upgrade head
uvicorn app.main:app --app-dir backend --reload --port 8000
python backend/seed.py
```

---

## Pruebas Automatizadas

Las 9 suites de prueba en `backend/tests/` utilizan SQLite en memoria (`sqlite+aiosqlite:///:memory:`) y archivos temporales para validar migraciones Alembic, seguridad DevSecOps, seeding y contratos HTTP:

```powershell
cd backend
pytest -v
```

---

## Variables de Entorno Clave

Ademas de las definidas en `.env.example` (que usa valores 100% ficticios), la configuracion en `app/config.py` soporta:

```env
ENVIRONMENT=development
DATABASE_URL=postgresql+asyncpg://example_user:example_pass@db.example.local:5432/ctf_example
DB_ECHO=false
AUTO_SEED_ENABLED=true
JWT_SECRET=example_jwt_secret_replace_with_32_plus_random_chars
FLAG_HMAC_SECRET=example_flag_hmac_secret_replace_with_32_plus_chars
TRUSTED_PROXY_COUNT=1
CORS_ORIGINS=http://localhost:3000,https://portal.example.test
CORS_ORIGIN_REGEX=
CHALLENGES_BASE_URL=https://challenges.example.test
CHALLENGES_REPOSITORY=example-org/example-ctf-challenges
```

Nota de seguridad: Nunca reutilizar `JWT_SECRET`, `FLAG_HMAC_SECRET` ni credenciales de ejemplo de desarrollo en despliegues publicos. Consulta [Estandares DevSecOps](../docs/STANDARDS.md) para el patron de integracion BFF sin exposicion de tokens en navegador.
