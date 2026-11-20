# EclipSec CTF - Backend API Service

Servicio backend asincrono construido con **FastAPI**, **SQLAlchemy (Async)** y **PostgreSQL / SQLite**, disenado para ejecutarse en **Railway** e integrarse de forma segura con el portal web **EclipSec** (`eclipsec.cl`) y el cliente **eclipsecCLI**.

---

## Capacidades Principales

1. **Autenticacion y Telemetria**:
   - Registro y autenticacion con hashing de contraseñas via `bcrypt` y emision de JWT (`HS256`).
   - Registro de `nationality`, puntaje acumulado (`score`), fecha de ingreso (`created_at`) y ultima conexion (`last_connected_at`).
2. **Gestion de Retos, Instancias CLI y Validacion de Flags**:
   - Catalogo filtrable por categoria y dificultad con resolucion dinamica de `target_url` via `CHALLENGES_BASE_URL`.
   - Verificacion de flags en tiempo constante mediante `hmac.compare_digest` y prevencion de doble puntuacion (`uq_user_challenge_solve`).
   - Registro idempotente de sesiones locales (`/start`, `/stop`) con metadatos de repositorio (`repository`, `path`, `version`) para `eclipsecCLI`.
3. **Leaderboard y Perfiles**:
   - Ranking global ordenado por `score DESC`, desempate por `last_solve_at ASC NULLS LAST` y `created_at ASC`.
   - Estadisticas agregadas por nacionalidad (`/api/v1/leaderboard/countries`) y perfiles de jugador (`/api/v1/users/{username}/profile`).
4. **Administracion RBAC y Adaptador Legacy**:
   - CRUD completo de retos y administracion de usuarios bajo rol `admin` (`/api/v1/admin/*`).
   - Adaptador de compatibilidad en `POST /api/ctf-academy`.

Para revisar la referencia completa de contratos, payloads y las mejoras de seguridad planificadas, consulta [Referencia de la API](../docs/API_REFERENCE.md) y la [Auditoria Tecnica](../docs/PROJECT_AUDIT.md).

---

## Resumen de Endpoints

| Grupo | Prefijo | Endpoints Principales |
|---|---|---|
| Salud | `/` | `GET /`, `GET /health` |
| Autenticacion | `/api/v1/auth` | `POST /register`, `POST /login`, `GET /me`, `PUT /me` |
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
python seed.py
uvicorn app.main:app --reload --port 8000
```

Documentacion interactiva disponible en `http://localhost:8000/docs`.

El backend resuelve automaticamente sus rutas de `.env`, `ctf.db` y `seed.py` con `pathlib.Path`, por lo que tambien funciona ejecutandolo desde la raiz del repositorio en Windows, Linux o macOS:

```bash
uvicorn app.main:app --app-dir backend --reload --port 8000
python backend/seed.py
```

---

## Pruebas Automatizadas

Las suites de prueba estan ubicadas en `backend/tests/` (`test_auth.py`, `test_challenges.py`, `test_instances.py`, `test_leaderboard.py`, `test_users.py`, `test_admin.py`) y utilizan SQLite en memoria (`sqlite+aiosqlite:///:memory:`).

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
JWT_SECRET=example_jwt_secret_replace_with_32_plus_random_chars
CORS_ORIGINS=http://localhost:3000,https://portal.example.test
CORS_ORIGIN_REGEX=
CHALLENGES_BASE_URL=https://challenges.example.test
CHALLENGES_REPOSITORY=example-org/example-ctf-challenges
```

Nota de seguridad: Nunca reutilizar `JWT_SECRET` ni credenciales de ejemplo de desarrollo en despliegues publicos. Consulta [Estandares DevSecOps](../docs/STANDARDS.md) para el patron de integracion BFF sin exposicion de tokens en navegador.
