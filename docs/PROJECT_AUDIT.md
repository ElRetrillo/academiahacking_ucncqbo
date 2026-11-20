# Auditoria Tecnica del Proyecto y Hoja de Ruta

**Repositorio:** `academiahacking_ucncqbo`
**Rama de trabajo:** `feat/ctf-standards-and-docs` (originada desde `main` `da64c94`)
**Fecha de actualizacion:** 2026-11-20
**Alcance:** Backend API (`backend/`), migraciones (`backend/alembic/`), infraestructura de contenedores (`docker/`), configuracion de despliegue (`railway.toml`, `backend/railway.json`) y documentacion.

---

## 1. Resumen Ejecutivo

El repositorio contiene dos componentes operativos del ecosistema CTF **EclipSec** (Academia de Hacking Competitivo UCN Coquimbo):

1. **Backend API (`backend/`)**: Servicio REST asincrono en FastAPI con arquitectura desacoplada por capas (Routers -> Servicios -> Repositorios `Protocol` + SQLAlchemy Async -> PostgreSQL/SQLite + Alembic), autenticacion JWT con cookies `HttpOnly` + CSRF, verificacion `HMAC-SHA256` de flags, ranking SQL unificado, registro de sesiones locales para `eclipsecCLI`, administracion RBAC y adaptador heredado (`POST /api/ctf-academy`).
2. **Entorno de Retos Docker (`docker/`)**: 11 retos web (`web-001` a `web-011`) empaquetados como servicios individuales en `docker/challenge-web-001..011`, un entorno consolidado para Railway en `docker/monolithic/` y un `docker/docker-compose.yml` para despliegue local o en VPS.

El portal web frontend (`eclipsec.cl` en Vercel), el cliente CLI (`eclipsecCLI`) y el repositorio de retos descargables (`ElRetrillo/retos_ctf`) residen en repositorios externos.

### Inventario Actual de Artefactos

| Area | Archivos / Cantidad | Estado Observado |
|---|---|---|
| Configuracion y Calidad (`backend/`) | `config.py`, `database.py`, `main.py`, `pyproject.toml`, `alembic.ini` | Validacion fail-fast en produccion, `PRAGMA foreign_keys=ON` en SQLite, `pool_pre_ping` en PostgreSQL y healthcheck con `SELECT 1` |
| Migraciones (`backend/alembic/`) | `env.py`, `script.py.mako`, `versions/0001_initial_schema.py` | Esquema versionado declarativamente para todas las tablas e indices compuestos |
| Modelos ORM (`backend/app/models/`) | 6 archivos (`base_utils.py`, `user.py`, `challenge.py`, `solve.py`, `instance.py`, `revoked_token.py`) | Indices compuestos para ranking/filtros/envios, cascada completa y tabla `revoked_tokens` |
| Repositorios (`backend/app/repositories/`) | 5 archivos (`protocols.py`, `user_repository.py`, `challenge_repository.py`, `leaderboard_repository.py`, `token_repository.py`) | Acceso a datos aislado tras interfaces `Protocol`, updates atomicos SQL y manejo de `IntegrityError` |
| Schemas Pydantic (`backend/app/schemas/`) | 4 modulos (`auth.py`, `challenge.py`, `leaderboard.py`, `user.py`) | `@computed_field` para compatibilidad `camelCase`, limite UTF-8 de 72 bytes para bcrypt, validacion de URLs/paths/dificultades |
| Servicios (`backend/app/services/`) | 7 archivos (`auth_service.py`, `challenge_service.py`, `ctf_academy_service.py`, `leaderboard_service.py`, `rate_limiter.py`, `security.py`, `user_service.py`) | Inyeccion de dependencias por constructor, estrategia `HmacFlagVerifier` y rate limiter con cota de memoria y proteccion `TRUSTED_PROXY_COUNT` |
| Routers API (`backend/app/api/v1/`) | 6 routers (`auth.py`, `challenges.py`, `leaderboard.py`, `users.py`, `admin.py`, `ctf_academy.py`) | Routers delgados sin acceso directo a SQLAlchemy, protegidos con cookies `HttpOnly`, CSRF y rate limiting |
| Pruebas (`backend/tests/`) | 9 suites (`test_admin.py`, `test_auth.py`, `test_challenges.py`, `test_instances.py`, `test_leaderboard.py`, `test_migrations.py`, `test_security_hardening.py`, `test_seed_and_health.py`, `test_users.py`) | Ejecutadas con `pytest -v` bajo `Python 3.13.14` (`win_amd64`) |
| Retos sembrados (`backend/seed.py`) | 12 retos (`web-001`..`web-011` + `web-sqli-001`) | Sincronizacion idempotente no destructiva, almacenamiento `[REDACTED]` + `HMAC-SHA256` y fail-fast en produccion |
| Contenedores individuales (`docker/challenge-web-*`) | 11 carpetas (`001` a `011`) | Dockerfiles reparados, `ttyd` removido, usuario no-root `ctf` y flags por `ARG` |
| Contenedor monolitico (`docker/monolithic/`) | `Dockerfile`, `start.sh`, `web-001`..`web-011` | Aislado por UID (`web002`..`web011`), sin `ttyd` ni `ENV FLAG=` global |
| Metadatos locales en Git | `.atl/` | Eliminado de Git e ignorado en `.gitignore` (Fase 2) |

---

## 2. Hallazgos de Seguridad (DevSecOps)

### Severidad Critica

#### SEC-01: [MITIGADO PARCIALMENTE] Aislamiento entre retos en contenedores CTF
- **Ubicacion:** [docker/monolithic/Dockerfile](../docker/monolithic/Dockerfile), [docker/monolithic/start.sh](../docker/monolithic/start.sh), [docker/challenge-web-001/Dockerfile](../docker/challenge-web-001/Dockerfile)
- **Estado actual:** Se elimino `ttyd` y la shell `root` de todos los contenedores victima, se elimino `ENV FLAG=` global, se asignaron UIDs dedicados (`web002`..`web011` en monolitico y `ctf` en standalone) con permisos `0550`/`0440` (`0700` en `web-006` para SQLite), se retiro `/app/web-005/flag.txt` para forzar path traversal en LFI y se parametrizaron las flags mediante `ARG`.
- **Pendiente (Fase 5):** Anadir limites de recursos (`mem_limit`, `cpus`, `pids_limit`) y rootfs de solo lectura donde aplique, mas estandar UI/HTML con `global.css` 60-30-10.

#### SEC-02: [RESUELTO en Fase 3] Flags en base de datos y externalizacion de secretos
- **Ubicacion:** [backend/seed.py](../backend/seed.py), [backend/app/services/security.py](../backend/app/services/security.py), [backend/app/services/challenge_service.py](../backend/app/services/challenge_service.py)
- **Estado actual:** La base de datos almacena `flag="[REDACTED]"` y `flag_hash` calculado con `HMAC-SHA256` (`FLAG_HMAC_SECRET`). Los envios en `submissions` guardan el hash HMAC y nunca el texto enviado. `ChallengeAdmin` expone `flag="[REDACTED]"` + `flag_configured`. En `ENVIRONMENT="production"`, `seed.py` exige flags externas via variables `FLAG_<SLUG>` o `CHALLENGES_FLAGS_FILE` (fallando si faltan); las flags por defecto en codigo solo quedan para desarrollo local.

#### SEC-03: [RESUELTO en Fase 3] Secretos inseguros por defecto sin validacion fail-fast en produccion
- **Ubicacion:** [backend/app/config.py](../backend/app/config.py)
- **Estado actual:** `Settings.validate_production_security` aborta el arranque (`ValueError`) si `ENVIRONMENT == "production"` y `JWT_SECRET` o `FLAG_HMAC_SECRET` son menores a 32 caracteres o contienen marcadores de desarrollo/ejemplo, o si `COOKIE_SAMESITE == "none"` sin cookie `Secure`.

#### SEC-04: [RESUELTO en Fase 3-4] Escalacion de privilegios y proteccion de cuentas admin
- **Ubicacion:** [backend/app/services/auth_service.py](../backend/app/services/auth_service.py), [backend/app/services/user_service.py](../backend/app/services/user_service.py), [backend/seed.py](../backend/seed.py)
- **Estado actual:** `ALLOW_FIRST_USER_ADMIN` es `False` por defecto; todo registro publico asigna `role = "user"`. `ensure_admin_user()` aprovisiona al administrador inicial evitando colisiones de `username`/`email` y exigiendo contrasena robusta (>= 12 caracteres, <= 72 bytes UTF-8) en produccion. `UserAdminUpdate` restringe valores validos (`Literal["user", "admin"]`, `score >= 0`) e impide que un admin se auto-desactive o auto-degrade.

---

### Severidad Alta

#### SEC-05: [RESUELTO en Fase 3-4] Exposicion de tokens JWT, revocacion y poda de tokens expirados
- **Ubicacion:** [backend/app/api/v1/auth.py](../backend/app/api/v1/auth.py), [backend/app/api/v1/ctf_academy.py](../backend/app/api/v1/ctf_academy.py), [backend/app/repositories/token_repository.py](../backend/app/repositories/token_repository.py)
- **Estado actual:** `POST /api/v1/auth/session/login` y `POST /api/ctf-academy` emiten cookies `HttpOnly; SameSite=Lax` (`Secure` en produccion) + cookie CSRF (`eclipsec_csrf`) sin devolver tokens JWT en el payload JSON hacia navegadores. Todo token incluye `jti` y `typ` (`"web"` de 60 min o `"cli"` de 12 h); `SqlAlchemyTokenRevocationRepository` revoca de forma idempotente y poda registros ya expirados.

#### SEC-06: [RESUELTO en Fase 3] Configuracion CORS restrictiva y cabeceras HTTP
- **Ubicacion:** [backend/app/main.py](../backend/app/main.py), [backend/app/config.py](../backend/app/config.py)
- **Estado actual:** `CORS_ORIGIN_REGEX` vacio por defecto, validacion fail-fast contra `*` y wildcards abiertos en produccion, metodos y cabeceras acotados y middleware HTTP de seguridad (`nosniff`, `DENY`, `Referrer-Policy`, `Permissions-Policy`, `HSTS` en produccion y `Cache-Control: no-store` en rutas sensibles).

#### SEC-07: [RESUELTO en Fase 3] Ocultamiento de PII en perfil publico
- **Ubicacion:** [backend/app/api/v1/users.py](../backend/app/api/v1/users.py), [backend/app/schemas/user.py](../backend/app/schemas/user.py)
- **Estado actual:** `GET /api/v1/users/{username}/profile` retorna `UserPublicProfileDetail` sin `email`, `role`, `is_active` ni `last_connected_at`, reservando dichos campos para `/api/v1/auth/me` y `/api/v1/admin/users`.

#### SEC-08: [RESUELTO en Fase 3-4] Limitacion de tasa resistente a falsificacion de IP y fuga de memoria
- **Ubicacion:** [backend/app/services/rate_limiter.py](../backend/app/services/rate_limiter.py)
- **Estado actual:** `InMemorySlidingWindowRateLimiter` acota la cantidad de claves activas (`max_keys = 10_000`) mediante poda de buckets expirados y desalojo LRU. `get_client_ip()` respeta `TRUSTED_PROXY_COUNT` (`0` por defecto ignora `X-Forwarded-For`; `N > 0` extrae el salto agregado por el proxy confiable en `ips[-N]`), evitando bypass por spoofing de cabecera.

#### SEC-09: [RESUELTO en Fase 3] Contenedor de backend multi-stage non-root con `$PORT`
- **Ubicacion:** [backend/Dockerfile](../backend/Dockerfile)
- **Estado actual:** Build multi-stage sin compiladores en runtime, ejecucion bajo `appuser` y arranque respetando `${PORT:-8080}`.

---

### Severidad Media y Robustez

#### SEC-10: [RESUELTO en Fase 3-4] Validacion de entrada, limite 72 bytes de bcrypt e integridad referencial
- **Ubicacion:** [backend/app/schemas/](../backend/app/schemas/), [backend/app/services/security.py](../backend/app/services/security.py), [backend/app/services/ctf_academy_service.py](../backend/app/services/ctf_academy_service.py), [backend/app/database.py](../backend/app/database.py)
- **Estado actual:**
  - `hash_password` y los DTOs (`RegisterRequest`, `UserUpdate`, `CtfAcademyService`) validan el limite de 72 bytes UTF-8 de `bcrypt 5.0.0`, y `verify_password` rechaza cadenas mayores sin provocar `ValueError`.
  - `RegisterRequest` normaliza `email` a minusculas y previene duplicados case-insensitive de `username` y `email`.
  - `ChallengeCreate` y `ChallengeUpdate` validan esquemas seguros de `target_url` (bloqueando `javascript:`, `//`), `difficulty`, `category`, `path` sin `..` ni `/` inicial y rechazo de `flag` vacia o `[REDACTED]`.
  - `CtfAcademyService` captura `ValidationError` en `login` y normaliza timestamps Naive/UTC con `to_utc_millis`.
  - SQLite activa `PRAGMA foreign_keys=ON` y el modelo `User` incluye cascada hacia `ChallengeInstance`.

#### SEC-11: [RESUELTO en Fase 3] Throttling de escritura en `last_connected_at`
- **Ubicacion:** [backend/app/api/deps.py](../backend/app/api/deps.py), [backend/app/repositories/user_repository.py](../backend/app/repositories/user_repository.py)
- **Estado actual:** `touch_last_connected` aplica ventana minima de 60 segundos antes de persistir cambios en `users.last_connected_at`.

---

## 3. Defectos Funcionales y Deuda Tecnica

1. **[RESUELTO en Fase 2]** Dockerfiles individuales reparados, unificacion `web-009` a `/index.bak`, flags `web-004`/`web-011` aisladas, red compose y retiro de `.atl/`.
2. **[RESUELTO en Fase 2]** Alineacion de Railway (`railway.toml`, `backend/railway.json`), `.env.example` 100% ficticio, `.gitattributes` LF y rutas portables multi-SO.
3. **[RESUELTO en Fase 4] Unificacion y optimizacion del calculo de ranking en SQL (`O(1)` memoria)**:
   - [backend/app/repositories/leaderboard_repository.py](../backend/app/repositories/leaderboard_repository.py) centraliza `get_global_entries` y `get_user_global_rank`, empatando los criterios `score DESC`, `last_solve_at ASC`, `created_at ASC`, `id ASC` en una consulta agregada SQL utilizada uniformemente por `LeaderboardService`, `UserService` y `CtfAcademyService`.
4. **[RESUELTO en Fase 4] Migraciones declarativas Alembic, seed idempotente y healthcheck real de BD**:
   - Reemplazado el parche DDL ad-hoc por [backend/alembic/versions/0001_initial_schema.py](../backend/alembic/versions/0001_initial_schema.py), agregados indices compuestos e indexacion en `revoked_tokens.expires_at`.
   - `sync_seed_data()` en [backend/seed.py](../backend/seed.py) sincroniza retos faltantes sin destruir ediciones existentes.
   - `GET /health` en [backend/app/main.py](../backend/app/main.py) ejecuta `SELECT 1` devolviendo `503` si la base de datos falla, y `DB_ECHO` es `False` por defecto.
5. **[RESUELTO en Fase 4] Refactorizacion Clean Code, SOLID y proteccion contra condiciones de carrera**:
   - Introducida la capa `backend/app/repositories/` (`Protocol` + implementaciones SQLAlchemy Async), inyectada via `Depends` desde [backend/app/api/deps.py](../backend/app/api/deps.py); eliminados todos los imports de SQLAlchemy en `backend/app/api/v1/*.py`.
   - Actualizaciones atomicas SQL (`solves_count + 1`, `score + points`) y manejo de `IntegrityError` en `record_correct_solve`, `register_user` y `admin_create_challenge`.
   - `@computed_field` de Pydantic v2 en [backend/app/schemas/user.py](../backend/app/schemas/user.py) elimina la duplicacion manual de propiedades `camelCase` en servicios.
   - Configuracion [backend/pyproject.toml](../backend/pyproject.toml) agregada y finales de linea LF normalizados en todo el backend.
6. **Pendiente (Fase 5) — Limites en contenedores e interfaces HTML de retos (`docker/`)**:
   - Agregar limites de recursos y estandarizar HTML/CSS de los 11 retos web con `global.css` 60-30-10, HTML semantico y `<meta name="robots" content="noindex, nofollow">` manteniendo intactas todas las vulnerabilidades intencionales.

---

## 4. Hoja de Ruta Incremental (Paso a Paso)

| Fase | Objetivo Principal | Entregables y Criterios de Cierre |
|---|---|---|
| **Fase 1 (Completada)** | Auditoria, rama nueva y documentacion | Rama `feat/ctf-standards-and-docs` creada; suite `docs/*.md`, `README.md` y `backend/README.md` validados sin emojis ni flags expuestas. |
| **Fase 2 (Completada)** | Higiene, Docker anti-bypass y portabilidad | Retiro de `.atl/`; `.gitattributes` LF y rutas portables multi-SO en `backend/`; remocion de `ttyd`, aislamiento por UID, correccion `web-005`/`006`/`008`/`010`, flags por `ARG`, alineacion Railway y `.env.example` ficticio. |
| **Fase 3 (Completada)** | Endurecimiento DevSecOps del Backend | Validacion fail-fast de secretos; eliminacion de auto-admin; cookies `HttpOnly` + CSRF y revocacion `jti`; CORS estricto y cabeceras HTTP; rate limiting; ocultamiento de PII publica; `HMAC-SHA256` en flags/envios; `backend/Dockerfile` non-root multi-stage con `$PORT`. |
| **Fase 4 (Completada)** | Correccion de errores, Clean Code, SOLID, Alembic y pruebas | Capa Repository (`Protocol`) + DI (`Depends`) sin SQLAlchemy en routers; ranking SQL unificado; Alembic + indices compuestos + `PRAGMA foreign_keys=ON`; updates atomicos anti-carrera; proteccion bcrypt 72B, `TRUSTED_PROXY_COUNT` y rate limiter acotado; `GET /health` con check de BD; seed idempotente; 9 suites `pytest` y Alembic validados. |
| **Fase 5 (Siguiente)** | Contenedores dedicados con limites y estandar UI/HTML | Limites de recursos (`mem_limit`, `cpus`, `pids_limit`) y rootfs read-only en `docker/`; `global.css` 60-30-10 y HTML semantico con `noindex` en las interfaces web de retos sin comprometer la vulnerabilidad intencional de cada ejercicio. |
| **Fase 6** | Integracion integral Frontend (`eclipsec.cl`) y CLI | Verificacion extremo a extremo con frontend Next.js (BFF sin tokens en navegador, componentes genericos, skeletons, SEO, tipografia) y `eclipsecCLI`. |
