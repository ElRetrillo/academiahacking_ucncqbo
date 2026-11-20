# Auditoria Tecnica del Proyecto y Hoja de Ruta

**Repositorio:** `academiahacking_ucncqbo`
**Rama de analisis:** `main` (commit `da64c94`)
**Fecha de auditoria:** 2026-11-20
**Alcance:** Backend API (`backend/`), infraestructura de contenedores (`docker/`), configuracion de despliegue (`railway.toml`, `backend/railway.json`) y documentacion raiz.

---

## 1. Resumen Ejecutivo

El repositorio contiene dos componentes operativos del ecosistema CTF **EclipSec** (Academia de Hacking Competitivo UCN Coquimbo):

1. **Backend API (`backend/`)**: Servicio REST asincrono en FastAPI con SQLAlchemy Async (SQLite en desarrollo, PostgreSQL en produccion) que gestiona autenticacion JWT, catalogo de retos, validacion de flags, registro de sesiones locales para `eclipsecCLI`, ranking global/por pais, perfiles de jugador, administracion RBAC y un adaptador heredado (`POST /api/ctf-academy`).
2. **Entorno de Retos Docker (`docker/`)**: 11 retos web (`web-001` a `web-011`) empaquetados como servicios individuales en `docker/challenge-web-001..011`, un entorno consolidado para Railway en `docker/monolithic/` y un `docker/docker-compose.yml` para despliegue local o en VPS.

El portal web frontend (`eclipsec.cl` en Vercel), el cliente CLI (`eclipsecCLI`) y el repositorio de retos descargables (`ElRetrillo/retos_ctf`) residen en repositorios externos.

### Inventario Actual de Artefactos

| Area | Archivos / Cantidad | Estado Observado |
|---|---|---|
| Modelos ORM (`backend/app/models/`) | 5 archivos (`user.py`, `challenge.py`, `solve.py`, `instance.py`, `revoked_token.py`) | Operativo, con tabla `revoked_tokens` para revocacion por `jti` |
| Schemas Pydantic (`backend/app/schemas/`) | 4 archivos (`auth.py`, `challenge.py`, `leaderboard.py`, `user.py`) | Segregacion publica `UserPublicProfileDetail` y flags redactadas en admin |
| Servicios (`backend/app/services/`) | 6 archivos (`auth_service.py`, `challenge_service.py`, `leaderboard_service.py`, `rate_limiter.py`, `security.py`, `user_service.py`) | Operativo con estrategia `HmacFlagVerifier` y rate limiter deslizante |
| Routers API (`backend/app/api/v1/`) | 6 routers (`auth.py`, `challenges.py`, `leaderboard.py`, `users.py`, `admin.py`, `ctf_academy.py`) | Endurecidos con cookies `HttpOnly`, CSRF y rate limiting (pendiente refactor SOLID Fase 4) |
| Pruebas (`backend/tests/`) | 7 suites (`test_auth.py`, `test_challenges.py`, `test_instances.py`, `test_leaderboard.py`, `test_users.py`, `test_admin.py`, `test_security_hardening.py`) | Ejecutadas con `pytest -v` bajo `Python 3.13.14` (`win_amd64`) |
| Retos sembrados (`backend/seed.py`) | 12 retos (`web-001`..`web-011` + `web-sqli-001`) | Almacenamiento en BD solo `[REDACTED]` + `HMAC-SHA256`; produccion exige overrides externos |
| Contenedores individuales (`docker/challenge-web-*`) | 11 carpetas (`001` a `011`) | Dockerfiles reparados, `ttyd` removido, usuario no-root `ctf` y flags por `ARG` |
| Contenedor monolitico (`docker/monolithic/`) | `Dockerfile`, `start.sh`, `web-001`..`web-011` | Aislado por UID (`web002`..`web011`), sin `ttyd` ni `ENV FLAG=` global |
| Metadatos locales en Git | `.atl/` | Eliminado de Git e ignorado en `.gitignore` (Fase 2) |

### Estado de Ejecucion de Pruebas

Las 7 suites de `backend/tests/` se ejecutan mediante el entorno virtual local `backend/.venv` sobre SQLite en memoria (`sqlite+aiosqlite:///:memory:`), cubriendo contratos `/api/v1/*`, `/api/ctf-academy`, sesiones `HttpOnly` + CSRF, revocacion `jti`, rate limiting, validacion fail-fast de produccion, ocultamiento de PII publica y verificacion `HMAC-SHA256`.

---

## 2. Hallazgos de Seguridad (DevSecOps)

### Severidad Critica

#### SEC-01: [MITIGADO PARCIALMENTE] Aislamiento entre retos en contenedores CTF
- **Ubicacion:** [docker/monolithic/Dockerfile](../docker/monolithic/Dockerfile), [docker/monolithic/start.sh](../docker/monolithic/start.sh), [docker/challenge-web-001/Dockerfile](../docker/challenge-web-001/Dockerfile)
- **Estado actual:** Se elimino `ttyd` y la shell `root` de todos los contenedores victima, se elimino `ENV FLAG=` global, se asignaron UIDs dedicados (`web002`..`web011` en monolitico y `ctf` en standalone) con permisos `0550`/`0440` (`0700` en `web-006` para SQLite), se retiro `/app/web-005/flag.txt` para forzar path traversal en LFI y se parametrizaron las flags mediante `ARG`.
- **Pendiente (Fase 5):** Separar completamente cada reto en contenedores independientes con limites de recursos (`mem_limit`, `cpus`, `pids_limit`) y rootfs de solo lectura donde aplique, mas estandar UI/HTML.

#### SEC-02: [RESUELTO en Fase 3] Flags en base de datos y externalizacion de secretos
- **Ubicacion:** [backend/seed.py](../backend/seed.py), [backend/app/services/security.py](../backend/app/services/security.py#L24-L53), [backend/app/services/challenge_service.py](../backend/app/services/challenge_service.py)
- **Estado actual:** La base de datos almacena `flag="[REDACTED]"` y `flag_hash` calculado con `HMAC-SHA256` (`FLAG_HMAC_SECRET`). Los envios en `submissions` guardan el hash HMAC y nunca el texto enviado. `ChallengeAdmin` expone `flag="[REDACTED]"` + `flag_configured`. En `ENVIRONMENT="production"`, `seed.py` exige flags externas via variables `FLAG_<SLUG>` o `CHALLENGES_FLAGS_FILE` (fallando si faltan); las flags en codigo solo quedan como respaldo local de desarrollo.

#### SEC-03: [RESUELTO en Fase 3] Secretos inseguros por defecto sin validacion fail-fast en produccion
- **Ubicacion:** [backend/app/config.py](../backend/app/config.py#L88-L105)
- **Estado actual:** `Settings.validate_production_security` aborta el arranque (`ValueError`) si `ENVIRONMENT == "production"` y `JWT_SECRET` o `FLAG_HMAC_SECRET` son menores a 32 caracteres o contienen marcadores de desarrollo/ejemplo.

#### SEC-04: [RESUELTO en Fase 3] Escalacion de privilegios por auto-asignacion de administrador
- **Ubicacion:** [backend/app/services/auth_service.py](../backend/app/services/auth_service.py#L34-L38), [backend/seed.py](../backend/seed.py)
- **Estado actual:** `ALLOW_FIRST_USER_ADMIN` es `False` por defecto; todo registro publico asigna `role = "user"`. El administrador inicial solo se aprovisiona mediante `ensure_admin_user()` en `seed.py` exigiendo contrasena robusta (>= 12 caracteres, sin marcadores de ejemplo) en produccion.

---

### Severidad Alta

#### SEC-05: [RESUELTO en Fase 3] Exposicion de tokens JWT en navegador y ausencia de revocacion
- **Ubicacion:** [backend/app/api/v1/auth.py](../backend/app/api/v1/auth.py), [backend/app/api/v1/ctf_academy.py](../backend/app/api/v1/ctf_academy.py), [backend/app/models/revoked_token.py](../backend/app/models/revoked_token.py)
- **Estado actual:** `POST /api/v1/auth/session/login` y `POST /api/ctf-academy` emiten cookies `HttpOnly; SameSite=Lax` (`Secure` en produccion) + cookie CSRF (`eclipsec_csrf`) sin devolver tokens JWT en el payload JSON hacia navegadores. Todo token incluye `jti` y `typ` (`"web"` de 60 min o `"cli"` de 12 h), y `logout` revoca el `jti` en `revoked_tokens`.

#### SEC-06: [RESUELTO en Fase 3] Configuracion CORS restrictiva
- **Ubicacion:** [backend/app/main.py](../backend/app/main.py), [backend/app/config.py](../backend/app/config.py)
- **Estado actual:** `CORS_ORIGIN_REGEX` vacio por defecto, validacion fail-fast que bloquea `*` y wildcards abiertos `*.vercel.app` en produccion, metodos restringidos a `GET, POST, PUT, DELETE, OPTIONS`, cabeceras restringidas a `Authorization, Content-Type, X-CSRF-Token` y middleware HTTP de cabeceras de seguridad (`nosniff`, `DENY`, `Referrer-Policy`, `Permissions-Policy`, `HSTS` en produccion y `Cache-Control: no-store` en rutas sensibles).

#### SEC-07: [RESUELTO en Fase 3] Ocultamiento de PII en perfil publico
- **Ubicacion:** [backend/app/api/v1/users.py](../backend/app/api/v1/users.py#L10-L16), [backend/app/schemas/user.py](../backend/app/schemas/user.py)
- **Estado actual:** `GET /api/v1/users/{username}/profile` retorna `UserPublicProfileDetail` sin `email`, `role`, `is_active` ni `last_connected_at`, reservando dichos campos exclusivamente para `/api/v1/auth/me` y `/api/v1/admin/users`.

#### SEC-08: [RESUELTO en Fase 3] Limitacion de tasa (Rate Limiting)
- **Ubicacion:** [backend/app/services/rate_limiter.py](../backend/app/services/rate_limiter.py), [backend/app/api/v1/auth.py](../backend/app/api/v1/auth.py), [backend/app/api/v1/challenges.py](../backend/app/api/v1/challenges.py), [backend/app/api/v1/ctf_academy.py](../backend/app/api/v1/ctf_academy.py)
- **Estado actual:** Rate limiter de ventana deslizante en memoria aplicado a registro, login, envio de flags y acciones equivalentes de `/api/ctf-academy`, devolviendo `429 Too Many Requests` con cabecera `Retry-After`.

#### SEC-09: [RESUELTO en Fase 3] Contenedor de backend multi-stage non-root con `$PORT`
- **Ubicacion:** [backend/Dockerfile](../backend/Dockerfile)
- **Estado actual:** Build multi-stage sin compiladores en runtime, ejecucion bajo usuario sin privilegios `appuser` y arranque respetando `${PORT:-8080}`.

---

### Severidad Media

#### SEC-10: [RESUELTO en Fase 3] Error 500 y mensajes sanitizados en `POST /api/ctf-academy`
- **Ubicacion:** [backend/app/api/v1/ctf_academy.py](../backend/app/api/v1/ctf_academy.py)
- **Estado actual:** Validacion alineada a `>= 6` caracteres y manejo tipado de `ValidationError` y `HTTPException` sin exponer trazas ni detalles internos.

#### SEC-11: [RESUELTO en Fase 3] Throttling de escritura en `last_connected_at`
- **Ubicacion:** [backend/app/api/deps.py](../backend/app/api/deps.py)
- **Estado actual:** `touch_last_connected` aplica ventana minima de 60 segundos antes de persistir cambios en `users.last_connected_at`, eliminando escrituras en cada `GET`.

---

## 3. Defectos Funcionales y Deuda Tecnica

1. **[RESUELTO en Fase 2] Dockerfiles individuales rotos (`docker/challenge-web-002` a `challenge-web-011`)**: Eliminada la barra invertida suelta `\` de la linea 1 y corregido el escape de `$host`, `$remote_addr` y `$http_upgrade` en Nginx en los 10 Dockerfiles y en [docker/create_challenges.py](../docker/create_challenges.py).
2. **[RESUELTO en Fase 2] Desincronizacion entre retos standalone y monolitico**:
   - `web-009` unificado a `/index.bak` en [docker/challenge-web-009/app.py](../docker/challenge-web-009/app.py#L24) y [docker/monolithic/web-009/app.py](../docker/monolithic/web-009/app.py#L24).
   - `web-011` y `web-004` aprovisionan sus flags en build-time en `/app/web-011/flag.txt` y `/app/web-004/flag.txt` (monolitico) y `/app/flag.txt` (standalone), con pistas actualizadas en [backend/seed.py](../backend/seed.py) para evitar colision con `web-005` en `/flag.txt`.
3. **[RESUELTO en Fase 2] Configuracion de red incompleta en `docker/docker-compose.yml`**: Agregada `networks: [ctf-net]` a `web-001`, eliminado el bloque comentado muerto `misc-001` y hecha idempotente la generacion desde `docker/create_challenges.py`.
4. **[RESUELTO en Fase 2] Rutas locales hardcodeadas y artefactos personales en Git**: Reemplazadas rutas absolutas de desarrollador por `Path(__file__).resolve().parent` en [docker/build_monolithic.py](../docker/build_monolithic.py) y [docker/create_challenges.py](../docker/create_challenges.py), y eliminada `.atl/` del seguimiento Git e ignorada en `.gitignore`.
5. **Inconsistencia y complejidad `O(N)` en calculo de ranking**: [backend/app/services/user_service.py](../backend/app/services/user_service.py#L45-L60) y [backend/app/api/v1/ctf_academy.py](../backend/app/api/v1/ctf_academy.py#L104-L119) calculan el ranking cargando todos los `User.id` en Python y ordenando por `User.created_at.asc()`, lo cual diverge de [backend/app/services/leaderboard_service.py](../backend/app/services/leaderboard_service.py#L38-L42) que desempata por `last_solve_at.asc().nulls_last()`.
6. **Seeding no incremental y migraciones manuales sin Alembic**: [backend/app/main.py](../backend/app/main.py#L22-L34) solo ejecuta `seed()` cuando la tabla `challenges` tiene 0 registros; cualquier base ya desplegada no recibe nuevos retos agregados a `CHALLENGES_DATA` (como `web-sqli-001`). [backend/app/database.py](../backend/app/database.py#L46-L75) ejecuta `ALTER TABLE` manual en codigo de aplicacion sin versionado de esquema (Alembic).
7. **Violaciones de Clean Code y SOLID**:
   - Routers con logica de acceso a datos acoplada a SQLAlchemy (`admin.py`, `ctf_academy.py`).
   - Schemas con campos duplicados (`snake_case` y `camelCase` simultaneos en `UserPublicProfileDetail`, `UserProfileDetail` y `RecentSolveDetail` en `backend/app/schemas/user.py`).
   - Imports muertos en `leaderboard_service.py` (`datetime`, `nulls_last`); en Fase 3 se eliminaron `passlib[bcrypt]`, los imports muertos en `deps.py` y `challenge_service.py`, y el codigo comentado de `backend/seed.py`.
   - **[RESUELTO en Fase 2]** Alineados [railway.toml](../railway.toml) y [backend/railway.json](../backend/railway.json) (`restartPolicyMaxRetries = 10`, `healthcheckPath = "/health"`, `healthcheckTimeout = 100`), completado `backend/.env.example` con credenciales 100% ficticias, corregidos `web-010` (`X-Forwarded-For` multicapa) y `web-006` (SQLite con `Path` + `closing()`), y garantizada la portabilidad multi-SO (`.gitattributes` LF, `BACKEND_DIR` con `Path` y `.as_posix()` en `config.py`, `main.py` y `seed.py`).
8. **Deuda en interfaces HTML de retos (`docker/`)**: Estilos inline duplicados (`style="background:#1a1a2e;..."`), ausencia de `global.css` con tokens 60-30-10 y HTML sin estructura semantica ni `<meta name="robots" content="noindex, nofollow">`.

---

## 4. Hoja de Ruta Incremental (Paso a Paso)

Siguiendo la regla de no avanzar a la siguiente tarea sin finalizar y verificar la anterior, la remediacion se estructura en 6 fases secuenciales:

| Fase | Objetivo Principal | Entregables y Criterios de Cierre |
|---|---|---|
| **Fase 1 (Completada)** | Auditoria, rama nueva y documentacion | Rama `feat/ctf-standards-and-docs` creada; suite `docs/*.md`, `README.md` y `backend/README.md` validados sin emojis ni flags expuestas. |
| **Fase 2 (Completada)** | Higiene, Docker anti-bypass y portabilidad | Retiro de `.atl/`; `.gitattributes` LF y rutas portables multi-SO en `backend/`; remocion de `ttyd`, aislamiento por UID, correccion `web-005`/`006`/`008`/`010`, flags por `ARG`, alineacion Railway y `.env.example` ficticio. |
| **Fase 3 (Completada)** | Endurecimiento DevSecOps del Backend | Validacion fail-fast de `JWT_SECRET` y `FLAG_HMAC_SECRET`; eliminacion de auto-admin en registro; sesion segura via cookies `HttpOnly` + CSRF y revocacion `jti` (cero tokens expuestos en navegador); CORS estricto y cabeceras HTTP; rate limiting; eliminacion de PII publica; `HMAC-SHA256` en flags/envios; `backend/Dockerfile` non-root multi-stage con `$PORT` y 7 suites `pytest` en verde. |
| **Fase 4 (Siguiente)** | Refactorizacion Clean Code, SOLID y Pruebas | Capa Repository + inyeccion de dependencias; unificacion de ranking en SQL; migracion a Alembic y seed idempotente; limpieza de campos duales e imports muertos; cobertura de `/health` y migraciones; `ruff` + `mypy` + `pytest` en verde. |
| **Fase 5** | Contenedores dedicados con limites y estandar UI/HTML | Limites de recursos (`mem_limit`, `cpus`, `pids_limit`) y rootfs read-only; `global.css` 60-30-10 y HTML semantico con `noindex` en las interfaces web de retos sin comprometer la vulnerabilidad intencional de cada ejercicio. |
| **Fase 6** | Integracion integral Frontend (`eclipsec.cl`) y CLI | Verificacion extremo a extremo con frontend Next.js (BFF sin tokens en navegador, componentes genericos, skeletons, SEO, tipografia) y `eclipsecCLI`. |
