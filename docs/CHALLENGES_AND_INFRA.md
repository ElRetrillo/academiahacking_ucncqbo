# Catalogo de Retos, Docker e Infraestructura de Despliegue

Este documento detalla los 12 retos registrados en la plataforma, sus modos de ejecucion y los procedimientos de despliegue local y en la nube.

---

## 1. Catalogo de Retos Registrados (`backend/seed.py`)

Por seguridad, ninguna flag real se transcribe en la documentacion (ver politica de externalizacion de flags en [STANDARDS.md](./STANDARDS.md) y hallazgo `SEC-02` en [PROJECT_AUDIT.md](./PROJECT_AUDIT.md)).

| Slug | Titulo | Categoria | Dificultad | Puntos | Modo de Ejecucion | Target / Ruta |
|---|---|---|---|---|---|---|
| `web-001` | Hidden in Plain Sight | `web` | `EASY` | 100 | Hosted Web | `/web-001/` |
| `web-002` | Robots & Crawlers | `web` | `EASY` | 100 | Hosted Web | `/web-002/` |
| `web-003` | Cookie Tampering | `web` | `EASY` | 150 | Hosted Web | `/web-003/` |
| `web-004` | Ping of Death | `web` | `MEDIUM` | 250 | Hosted Web | `/web-004/` |
| `web-005` | LFI to RCE | `web` | `MEDIUM` | 300 | Hosted Web | `/web-005/` |
| `web-006` | SQLi Login Bypass | `web` | `MEDIUM` | 300 | Hosted Web | `/web-006/` |
| `web-007` | IDOR Profiles | `web` | `MEDIUM` | 250 | Hosted Web | `/web-007/` |
| `web-008` | Server-Side Template Injection | `web` | `HARD` | 450 | Hosted Web | `/web-008/` |
| `web-009` | Source Code Leak | `web` | `EASY` | 150 | Hosted Web | `/web-009/` |
| `web-010` | Headers Matter | `web` | `MEDIUM` | 250 | Hosted Web | `/web-010/` |
| `web-011` | Command Execution GET | `web` | `HARD` | 400 | Hosted Web | `/web-011/` |
| `web-sqli-001` | Login Bypass | `web` | `EASY` | 100 | Local CLI | `ElRetrillo/retos_ctf` (`web/sqli-001`) |

---

## 2. Topologias de Despliegue de Retos

### 2.1 Docker Compose (Entorno Local o VPS Dedicado)

Definido en [docker/docker-compose.yml](../docker/docker-compose.yml). Levanta cada reto `web-001` a `web-011` en contenedores separados sin privilegios (`ctf`), sin terminales interactivas dentro de los objetivos y parametrizando las flags mediante build-args (`FLAG_WEB_001` a `FLAG_WEB_011`):

- Aplicaciones Web: `8001` a `8011` (internamente puerto `80` tras Nginx + Flask).
- Si se requiere consola web para estudiantes, debe desplegarse en un contenedor atacante aislado aparte, nunca dentro de los contenedores victima.

### 2.2 Contenedor Monolitico con Nginx (Railway PaaS)

Definido en [docker/monolithic/](../docker/monolithic/Dockerfile). Dado que Railway expone un unico dominio por servicio en puertos `80`/`443`, este nodo enruta mediante Nginx bajo subrutas `/web-001/` a `/web-011/`.

**Aislamiento y Configuracion Actual:**
- Cada servicio Flask se ejecuta bajo un usuario dedicado sin privilegios (`web002` a `web011`), sin `ttyd`, sin `ENV FLAG=` global y con permisos `0550`/`0440` (`0700` en `web-006` para SQLite) para impedir movimiento lateral o lectura de flags de otros retos.
- Las flags se inyectan en build-time via `ARG FLAG_WEB_001`..`ARG FLAG_WEB_011`, manteniendo los valores por defecto solo para desarrollo local y permitiendo sobrescribirlos en despliegue real.
- En Fase 5 se agregaran limites de recursos (`mem_limit`, `cpus`, `pids_limit`) y rootfs de solo lectura donde aplique.

### 2.3 Retos Locales mediante `eclipsecCLI`

Introducido para retos como `web-sqli-001`:
1. El backend registra la sesion en `challenge_instances` mediante `POST /api/v1/challenges/{slug}/start` y entrega `repository`, `path` y `version`.
2. El CLI descarga los artefactos desde el repositorio publico configurado en `CHALLENGES_REPOSITORY` (`ElRetrillo/retos_ctf` por defecto) y levanta Docker en la maquina del jugador.
3. El backend nunca invoca el daemon de Docker.

---

## 3. Despliegue del Backend API en Railway

### Configuracion Actual

- Archivo raiz [railway.toml](../railway.toml) y archivo [backend/railway.json](../backend/railway.json) apuntan a `backend/Dockerfile` (`appuser`, build multi-stage y puerto dinamico `${PORT:-8080}`).
- Railway aprovisiona PostgreSQL inyectando `DATABASE_URL` (normalizada automaticamente por `Settings.assemble_db_connection` a `postgresql+asyncpg://`).
- El esquema de base de datos se gestiona formalmente con **Alembic** (`alembic upgrade head`). Al iniciar con `AUTO_SEED_ENABLED=true`, `app/main.py` sincroniza de manera idempotente el usuario admin (si aplica) y los retos faltantes mediante `sync_seed_data()`.
- `GET /health` ejecuta `SELECT 1` para verificar conectividad real de la base de datos antes de reportar servicio saludable.

### Variables de Entorno del Backend

| Variable | Descripcion | Requerida en Produccion |
|---|---|---|
| `PROJECT_NAME` | Nombre visible en OpenAPI | Opcional |
| `ENVIRONMENT` | `development` o `production` | Si |
| `DATABASE_URL` | Cadena de conexion PostgreSQL/SQLite | Si |
| `DB_ECHO` | Logging verbose SQL (`false` por defecto) | Opcional |
| `AUTO_SEED_ENABLED` | Activa `sync_seed_data()` al iniciar (`true` por defecto) | Opcional |
| `JWT_SECRET` | Clave secreta aleatoria de minimo 32 caracteres | Si (critica) |
| `FLAG_HMAC_SECRET` | Clave secreta HMAC-SHA256 de minimo 32 caracteres para flags | Si (critica) |
| `JWT_ALGORITHM` | Algoritmo de firma JWT (`HS256`) | Opcional |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Duracion de cookie de sesion web en minutos | Opcional |
| `CLI_TOKEN_EXPIRE_MINUTES` | Duracion de token CLI en minutos | Opcional |
| `CORS_ORIGINS` | Lista separada por comas de origenes web exactos | Si |
| `CORS_ORIGIN_REGEX` | Expresion regular estricta para origenes adicionales | Opcional (vacio por defecto) |
| `COOKIE_SAMESITE` | Politica SameSite (`lax`, `strict`, `none`) | Opcional |
| `TRUSTED_PROXY_COUNT` | Numero de proxies inversos confiables para `X-Forwarded-For` (`0` o `1` en Railway) | Opcional |
| `RATE_LIMIT_ENABLED` | Habilita control de tasa deslizante | Opcional |
| `CHALLENGES_BASE_URL` | URL base publica del nodo de retos para resolver rutas relativas `/web-00X/` | Si (si hay retos alojados) |
| `CHALLENGES_REPOSITORY` | Repositorio `owner/repo` para descarga local via CLI | Opcional (`ElRetrillo/retos_ctf`) |
| `CHALLENGES_FLAGS_FILE` | Ruta a JSON con flags de produccion (o variables `FLAG_<SLUG>`) | Si (si no usa `FLAG_<SLUG>`) |
| `ADMIN_USERNAME` | Usuario administrador inicial | Opcional |
| `ADMIN_EMAIL` | Correo administrador inicial | Opcional |
| `ADMIN_PASSWORD` | Credencial inicial segura (>= 12 chars, max 72B UTF-8) | Si en primer arranque |

---

## 4. Guia para Crear Nuevos Retos CTF

Todo nuevo reto agregado al ecosistema debe respetar las siguientes reglas:

1. **Estructura estandar del reto**:
   - `Dockerfile`: Basado en imagen minima (`python:3.12-slim` o equivalente), con usuario no privilegiado (`USER ctf`), sin herramientas de compilacion en runtime y con una unica flag aislada en su contexto.
   - `app/`: Codigo fuente minimo y limpio, sin exponer codigo o flags de otros desafios.
   - `README.md`: Descripcion tecnica para mantenedores y writeup interno fuera de la imagen publicada.
2. **Estandares de interfaz web (para retos de categoria Web)**:
   - Usar `global.css` respetando la regla **60-30-10**, HTML semantico valido (`<main>`, `<section>`, un `<h1>`) y `<meta name="robots" content="noindex, nofollow">`.
   - Cero emojis y cero estilos inline repetitivos.
3. **Frontera de vulnerabilidad**:
   - La vulnerabilidad pedagogica (ej. SQLi, IDOR, LFI) debe ser intencional y acotada a su proposito formativo; nunca dejar shells administrativas globales como `root`.
4. **Registro en catalogo**:
   - Agregar metadatos en el catalogo (`seed` o repositorio `retos_ctf`) manteniendo las flags de produccion fuera del repositorio publico mediante secretos de entorno.
