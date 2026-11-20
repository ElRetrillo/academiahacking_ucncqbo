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
| Modelos ORM (`backend/app/models/`) | 4 archivos (`user.py`, `challenge.py`, `solve.py`, `instance.py`) | Operativo, con esquema de flags en claro |
| Schemas Pydantic (`backend/app/schemas/`) | 4 archivos (`auth.py`, `challenge.py`, `leaderboard.py`, `user.py`) | Operativo, con campos duales `snake_case`/`camelCase` en perfil |
| Servicios (`backend/app/services/`) | 5 archivos (`auth_service.py`, `challenge_service.py`, `leaderboard_service.py`, `security.py`, `user_service.py`) | Operativo, metodos estaticos sin inyeccion de repositorios |
| Routers API (`backend/app/api/v1/`) | 6 routers (`auth.py`, `challenges.py`, `leaderboard.py`, `users.py`, `admin.py`, `ctf_academy.py`) | Operativo, mezcla de contratos REST v1 y RPC legacy |
| Pruebas (`backend/tests/`) | 6 suites (`test_auth.py`, `test_challenges.py`, `test_instances.py`, `test_leaderboard.py`, `test_users.py`, `test_admin.py`) | Cobertura parcial sobre `/api/v1/*`; 0 pruebas para `/api/ctf-academy`, `/health` y migraciones |
| Retos sembrados (`backend/seed.py`) | 12 retos (`web-001`..`web-011` + `web-sqli-001`) | Flags hardcodeadas en codigo fuente |
| Contenedores individuales (`docker/challenge-web-*`) | 11 carpetas (`001` a `011`) | Dockerfiles reparados, `ttyd` removido, usuario no-root `ctf` y flags por `ARG` |
| Contenedor monolitico (`docker/monolithic/`) | `Dockerfile`, `start.sh`, `web-001`..`web-011` | Aislado por UID (`web002`..`web011`), sin `ttyd` ni `ENV FLAG=` global |
| Metadatos locales en Git | `.atl/` | Eliminado de Git e ignorado en `.gitignore` (Fase 2) |

### Estado de Ejecucion de Pruebas

Durante esta auditoria la revision fue estatica sobre el codigo fuente. En el entorno Windows de inspeccion no se dispone de un interprete `python` ni `pytest` instalado en el `PATH` del entorno virtual del proyecto, por lo que no se ejecutaron las suites de `backend/tests/`. La habilitacion de un entorno reproducible y la ejecucion completa de pruebas forman parte del cierre obligatorio de la Fase 2/3.

---

## 2. Hallazgos de Seguridad (DevSecOps)

### Severidad Critica

#### SEC-01: [MITIGADO PARCIALMENTE] Aislamiento entre retos en contenedores CTF
- **Ubicacion:** [docker/monolithic/Dockerfile](../docker/monolithic/Dockerfile), [docker/monolithic/start.sh](../docker/monolithic/start.sh), [docker/challenge-web-001/Dockerfile](../docker/challenge-web-001/Dockerfile)
- **Estado actual:** Se elimino `ttyd` y la shell `root` de todos los contenedores victima, se elimino `ENV FLAG=` global, se asignaron UIDs dedicados (`web002`..`web011` en monolitico y `ctf` en standalone) con permisos `0550`/`0440` (`0700` en `web-006` para SQLite), se retiro `/app/web-005/flag.txt` para forzar path traversal en LFI y se parametrizaron las flags mediante `ARG`.
- **Pendiente (Fase 5):** Separar completamente cada reto en contenedores independientes con limites de recursos (`mem_limit`, `cpus`, `pids_limit`) y rootfs de solo lectura donde aplique, mas estandar UI/HTML.

#### SEC-02: Flags en texto plano dentro del repositorio Git y la base de datos
- **Ubicacion:** [backend/seed.py](../backend/seed.py), [backend/app/models/challenge.py](../backend/app/models/challenge.py#L28-L29), [backend/app/services/security.py](../backend/app/services/security.py#L22-L40), [docker/create_challenges.py](../docker/create_challenges.py)
- **Descripcion:** Todas las flags de los 12 retos estan versionadas en texto plano en `backend/seed.py` y en los scripts/Dockerfiles de `docker/`. En base de datos, `Challenge.flag` persiste la flag en claro y `Challenge.flag_hash` utiliza SHA-256 directo sin sal ni clave secreta HMAC. Asimismo, `verify_flag` evalua la comparacion en claro antes del hash, y `Submission.submitted_flag` almacena envios sin enmascarar.
- **Impacto:** Cualquier persona con acceso de lectura al repositorio (si es publico o filtrado), a un respaldo de base de datos o a `GET /api/v1/admin/challenges` obtiene todas las flags de la competencia.
- **Remediacion:** Externalizar las flags de produccion a secretos/variables seguras fuera de Git, almacenar verificadores con `HMAC-SHA256` usando una clave secreta de servidor (`FLAG_HMAC_SECRET`) o hashing con sal, y retirar la columna en texto plano tras la migracion.

#### SEC-03: Secretos inseguros por defecto sin validacion fail-fast en produccion
- **Ubicacion:** [backend/app/config.py](../backend/app/config.py#L17), [backend/app/config.py](../backend/app/config.py#L35)
- **Descripcion:** `JWT_SECRET` tiene un valor literal predecible (`"change-this-in-production-super-secret-ctf-key-2026"`) y `ADMIN_PASSWORD` usa `"admin123456"`. No existe validacion en el arranque que impida iniciar con `ENVIRONMENT == "production"` cuando estos valores no han sido sobrescritos.
- **Impacto:** Un despliegue con variables de entorno incompletas permite falsificar tokens JWT de cualquier usuario o administrador.
- **Remediacion:** Agregar un validador en `Settings` que aborte el inicio de la aplicacion si `ENVIRONMENT == "production"` y `JWT_SECRET` mantiene el valor de desarrollo o tiene longitud inferior a 32 bytes.

#### SEC-04: Escalacion de privilegios por auto-asignacion del primer administrador
- **Ubicacion:** [backend/app/services/auth_service.py](../backend/app/services/auth_service.py#L33-L37), [backend/seed.py](../backend/seed.py#L173-L193)
- **Descripcion:** El bloque de creacion del administrador en `seed.py` esta comentado. En su lugar, `AuthService.register_user` consulta el conteo de filas en `users` y asigna `role = "admin"` al primer usuario que se registre (incluso mediante el endpoint publico `POST /api/ctf-academy` con `action: "register"`). Esta comprobacion carece de bloqueo transaccional, presentando condicion de carrera.
- **Impacto:** En cualquier despliegue nuevo o tras un reinicio de base de datos, el primer atacante externo que llame al registro obtiene privilegios totales de administracion.
- **Remediacion:** Eliminar la promocion automatica en el registro publico y aprovisionar el administrador inicial exclusivamente mediante comando administrativo idempotente o variable de entorno controlada.

---

### Severidad Alta

#### SEC-05: Exposicion de tokens JWT en vistas de red del navegador y almacenamiento cliente
- **Ubicacion:** [backend/app/api/v1/auth.py](../backend/app/api/v1/auth.py#L22-L25), [backend/app/api/v1/ctf_academy.py](../backend/app/api/v1/ctf_academy.py#L242-L266), guias previas de integracion en `README.md` y `backend/README.md`
- **Descripcion:** Tanto `/api/v1/auth/login` como `/api/ctf-academy` devuelven el `access_token` JWT en el cuerpo JSON de respuesta para que el cliente web lo almacene en `localStorage` y lo envie en la cabecera `Authorization: Bearer`. Ademas, el token tiene validez de 7 dias (`ACCESS_TOKEN_EXPIRE_MINUTES = 10080`) y `logout` en `ctf_academy.py:270` no invalida la sesion.
- **Impacto:** Contraviene el principio de no exponer tokens en vistas de red desde navegadores ni en almacenamiento accesible via JavaScript (`localStorage`), ampliando el impacto de cualquier XSS al robo permanente de sesion sin capacidad de revocacion.
- **Remediacion:** Adoptar el patron **BFF (Backend for Frontend)** en Next.js o cookies emitidas por servidor con `HttpOnly; Secure; SameSite=Lax; Path=/`, rotacion/lista de revocacion por `jti`, expiracion corta de sesion web y tokens separados de alcance acotado exclusivamente para `eclipsecCLI`.

#### SEC-06: Configuracion CORS excesivamente permisiva con `allow_credentials=True`
- **Ubicacion:** [backend/app/main.py](../backend/app/main.py#L51-L58), [backend/app/config.py](../backend/app/config.py#L28)
- **Descripcion:** El middleware CORS habilita `allow_credentials=True`, `allow_methods=["*"]`, `allow_headers=["*"]` y la expresion regular `^https:\/\/.*\.vercel\.app$`.
- **Impacto:** Cualquier aplicacion alojada en cualquier subdominio de Vercel perteneciente a un tercero puede realizar peticiones autenticadas cross-origin contra la API.
- **Remediacion:** Restringir `CORS_ORIGINS` a dominios exactos controlados por EclipSec, limitar `CORS_ORIGIN_REGEX` a prefijos de proyecto propios y especificar listas explicitas de metodos y cabeceras permitidas.

#### SEC-07: Exposicion publica de datos personales (PII) en perfil de usuario
- **Ubicacion:** [backend/app/api/v1/users.py](../backend/app/api/v1/users.py#L11-L17), [backend/app/schemas/user.py](../backend/app/schemas/user.py#L65-L89)
- **Descripcion:** `GET /api/v1/users/{username}/profile` es publico sin autenticacion y devuelve `email`, `role`, `is_active` y `last_connected_at` dentro de `UserProfileDetail`.
- **Impacto:** Permite enumeracion de cuentas, recoleccion masiva de correos electronicos y mapeo de cuentas administrativas sin autenticacion.
- **Remediacion:** Crear un schema publico segregado (`UserPublicProfileDetail`) sin `email`, `role` ni `is_active`, reservando `email` exclusivamente para `/api/v1/auth/me` y `/api/v1/admin/users`.

#### SEC-08: Ausencia de limitacion de tasa (Rate Limiting) y proteccion anti fuerza bruta
- **Ubicacion:** [backend/app/api/v1/auth.py](../backend/app/api/v1/auth.py), [backend/app/api/v1/challenges.py](../backend/app/api/v1/challenges.py), [backend/app/api/v1/ctf_academy.py](../backend/app/api/v1/ctf_academy.py)
- **Descripcion:** Ningun endpoint de login, registro o envio de flags implementa limitacion de intentos ni bloqueo temporal.
- **Impacto:** Permite ataques automatizados de fuerza bruta sobre credenciales, creacion masiva de cuentas y enumeracion de flags.
- **Remediacion:** Incorporar rate limiting por IP y por usuario en `/auth/login`, `/auth/register`, `/challenges/{slug}/submit` y `/api/ctf-academy`.

#### SEC-09: Contenedor de backend ejecutado como `root`, sin multi-stage y con puerto fijo
- **Ubicacion:** [backend/Dockerfile](../backend/Dockerfile)
- **Descripcion:** El contenedor ejecuta `uvicorn` como `root`, mantiene `gcc` y `libpq-dev` en la imagen final y fija `--port 8080` en `CMD` sin leer la variable dinamica `$PORT` provista por Railway.
- **Impacto:** Aumenta la superficie de ataque en runtime y el tamano de imagen, y puede romper el enrutamiento si Railway asigna un puerto distinto a `8080`.
- **Remediacion:** Migrar a Dockerfile multi-stage con usuario sin privilegios (`appuser`) y arranque respetando `${PORT:-8080}`.

---

### Severidad Media

#### SEC-10: Error 500 y fuga de detalles internos en `POST /api/ctf-academy`
- **Ubicacion:** [backend/app/api/v1/ctf_academy.py](../backend/app/api/v1/ctf_academy.py#L223-L231), [backend/app/api/v1/ctf_academy.py](../backend/app/api/v1/ctf_academy.py#L300-L304)
- **Descripcion:** En `action == "register"`, la validacion manual permite contraseñas de longitud `>= 4`, pero acto seguido instancia `RegisterRequest` (que exige `min_length=6`) fuera del bloque `try/except`, disparando un `ValidationError` no capturado (HTTP 500). En `action == "complete"`, el bloque `except Exception as exc` devuelve `str(exc)` directamente en el mensaje HTTP 400.
- **Remediacion:** Alinear reglas de validacion, manejar `HTTPException` y `ValidationError` de forma tipada y devolver mensajes sanitizados sin detalles internos.

#### SEC-11: Escrituras en base de datos en peticiones de solo lectura
- **Ubicacion:** [backend/app/api/deps.py](../backend/app/api/deps.py#L31-L35), [backend/app/api/deps.py](../backend/app/api/deps.py#L70-L72), [backend/app/api/v1/ctf_academy.py](../backend/app/api/v1/ctf_academy.py#L197-L199)
- **Descripcion:** Cada peticion `GET` autenticada ejecuta `UPDATE users SET last_connected_at = ...` seguido de `commit()`.
- **Impacto:** Genera contencion de bloqueos de escritura en SQLite y carga transaccional innecesaria en PostgreSQL bajo trafico concurrente.
- **Remediacion:** Aplicar ventana minima de actualizacion (throttling de al menos 60 segundos entre actualizaciones de `last_connected_at`).

---

## 3. Defectos Funcionales y Deuda Tecnica

1. **[RESUELTO en Fase 2] Dockerfiles individuales rotos (`docker/challenge-web-002` a `challenge-web-011`)**: Eliminada la barra invertida suelta `\` de la linea 1 y corregido el escape de `$host`, `$remote_addr` y `$http_upgrade` en Nginx en los 10 Dockerfiles y en [docker/create_challenges.py](../docker/create_challenges.py).
2. **[RESUELTO en Fase 2] Desincronizacion entre retos standalone y monolitico**:
   - `web-009` unificado a `/index.bak` en [docker/challenge-web-009/app.py](../docker/challenge-web-009/app.py#L24) y [docker/monolithic/web-009/app.py](../docker/monolithic/web-009/app.py#L24).
   - `web-011` y `web-004` aprovisionan sus flags en build-time en `/app/web-011/flag.txt` y `/app/web-004/flag.txt` (monolitico) y `/app/flag.txt` (standalone), con pistas actualizadas en [backend/seed.py](../backend/seed.py) para evitar colision con `web-005` en `/flag.txt`.
3. **[RESUELTO en Fase 2] Configuracion de red incompleta en `docker/docker-compose.yml`**: Agregada `networks: [ctf-net]` a `web-001`, eliminado el bloque comentado muerto `misc-001` y hecha idempotente la generacion desde `docker/create_challenges.py`.
4. **[RESUELTO en Fase 2] Rutas locales hardcodeadas y artefactos personales en Git**: Reemplazadas rutas absolutas de desarrollador por `Path(__file__).resolve().parent` en [docker/build_monolithic.py](../docker/build_monolithic.py) y [docker/create_challenges.py](../docker/create_challenges.py), y eliminada `.atl/` del seguimiento Git e ignorada en `.gitignore`.
5. **Inconsistencia y complejidad `O(N)` en calculo de ranking**: [backend/app/services/user_service.py](../backend/app/services/user_service.py#L58-L70) y [backend/app/api/v1/ctf_academy.py](../backend/app/api/v1/ctf_academy.py#L128-L140) calculan el ranking cargando todos los `User.id` en Python y ordenando por `User.created_at.asc()`, lo cual diverge de [backend/app/services/leaderboard_service.py](../backend/app/services/leaderboard_service.py#L38-L42) que desempata por `last_solve_at.asc().nulls_last()`.
6. **Seeding no incremental y migraciones manuales sin Alembic**: [backend/app/main.py](../backend/app/main.py#L19-L30) solo ejecuta `seed()` cuando la tabla `challenges` tiene 0 registros; cualquier base ya desplegada no recibe nuevos retos agregados a `CHALLENGES_DATA` (como `web-sqli-001`). [backend/app/database.py](../backend/app/database.py#L46-L75) ejecuta `ALTER TABLE` manual en codigo de aplicacion sin versionado de esquema (Alembic).
7. **Violaciones de Clean Code y SOLID**:
   - Routers con logica de acceso a datos acoplada a SQLAlchemy (`admin.py`, `ctf_academy.py`).
   - Schemas con campos duplicados (`snake_case` y `camelCase` simultaneos en `UserProfileDetail` y `RecentSolveDetail` en `backend/app/schemas/user.py`).
   - Dependencia sin uso en `backend/requirements.txt` (`passlib[bcrypt]`), imports muertos (`OAuth2PasswordBearer` en `deps.py`, `update`/`delete` en `challenge_service.py`, `datetime`/`nulls_last` en `leaderboard_service.py`) y ~90 lineas de codigo comentado en `backend/seed.py`.
   - **[RESUELTO en Fase 2]** Alineados [railway.toml](../railway.toml) y [backend/railway.json](../backend/railway.json) (`restartPolicyMaxRetries = 10`, `healthcheckPath = "/health"`, `healthcheckTimeout = 100`), completado `backend/.env.example` con credenciales 100% ficticias, corregidos `web-010` (`X-Forwarded-For` multicapa) y `web-006` (SQLite con `Path` + `closing()`), y garantizada la portabilidad multi-SO (`.gitattributes` LF, `BACKEND_DIR` con `Path` y `.as_posix()` en `config.py`, `main.py` y `seed.py`).
8. **Deuda en interfaces HTML de retos (`docker/`)**: Estilos inline duplicados (`style="background:#1a1a2e;..."`), ausencia de `global.css` con tokens 60-30-10 y HTML sin estructura semantica ni `<meta name="robots" content="noindex, nofollow">`.

---

## 4. Hoja de Ruta Incremental (Paso a Paso)

Siguiendo la regla de no avanzar a la siguiente tarea sin finalizar y verificar la anterior, la remediacion se estructura en 6 fases secuenciales:

| Fase | Objetivo Principal | Entregables y Criterios de Cierre |
|---|---|---|
| **Fase 1 (Completada)** | Auditoria, rama nueva y documentacion | Rama `feat/ctf-standards-and-docs` creada; suite `docs/*.md`, `README.md` y `backend/README.md` validados sin emojis ni flags expuestas. |
| **Fase 2 (Completada)** | Higiene, Docker anti-bypass y portabilidad | Retiro de `.atl/`; `.gitattributes` LF y rutas portables multi-SO en `backend/`; remocion de `ttyd`, aislamiento por UID, correccion `web-005`/`006`/`008`/`010`, flags por `ARG`, alineacion Railway y `.env.example` ficticio. |
| **Fase 3 (Siguiente)** | Endurecimiento DevSecOps del Backend | Validacion fail-fast de `JWT_SECRET` en produccion; eliminacion de auto-admin en registro; sesion segura via BFF/cookies `HttpOnly` + CSRF (cero tokens expuestos en navegador); CORS estricto; rate limiting; eliminacion de PII en perfil publico; `HMAC-SHA256` y externalizacion de flags; `backend/Dockerfile` non-root multi-stage con `$PORT`. |
| **Fase 4** | Refactorizacion Clean Code, SOLID y Pruebas | Capa Repository + inyeccion de dependencias; unificacion de ranking en SQL; migracion a Alembic y seed idempotente; throttling de `last_connected_at`; limpieza de codigo muerto y campos duales; cobertura de tests incluyendo `/api/ctf-academy`, `/health` y migraciones; `ruff` + `mypy` + `pytest` en verde. |
| **Fase 5** | Contenedores dedicados con limites y estandar UI/HTML | Limites de recursos (`mem_limit`, `cpus`, `pids_limit`) y rootfs read-only; `global.css` 60-30-10 y HTML semantico con `noindex` en las interfaces web de retos sin comprometer la vulnerabilidad intencional de cada ejercicio. |
| **Fase 6** | Integracion integral Frontend (`eclipsec.cl`) y CLI | Verificacion extremo a extremo con frontend Next.js (BFF sin tokens en navegador, componentes genericos, skeletons, SEO, tipografia) y `eclipsecCLI`. |
