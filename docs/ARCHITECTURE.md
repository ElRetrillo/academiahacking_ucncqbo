# Arquitectura del Sistema EclipSec CTF

Este documento describe la arquitectura vigente del entorno **EclipSec CTF** (`academiahacking_ucncqbo`), su modelo de datos, los flujos principales de interaccion y su integracion verificada con el portal web (`EclipSec-WebPage`) y la CLI (`eclipsec-cli`).

---

## 1. Ecosistema General

La plataforma desacopla la capa de presentacion web, la API de negocio y la ejecucion de retos vulnerables:

```mermaid
flowchart LR
    Player["Jugador (Navegador Web)"] -->|"HTTPS (Cookie HttpOnly + X-CSRF-Token)"| Frontend["Portal Web EclipSec (React + Vite / Vercel)"]
    Frontend -->|"Fetch credentials:include / API REST"| Backend["Backend CTF API (FastAPI en Railway)"]
    Backend -->|"Async SQLAlchemy"| Database[("PostgreSQL Produccion / SQLite Dev")]

    Cli["eclipsec-cli (Maquina del Jugador)"] -->|"REST Bearer Acotado (typ=cli)"| Backend
    Cli -->|"Descarga Validada de Retos"| ChallengeRepo["Repositorio Publico de Retos (ElRetrillo/retos_ctf)"]
    Cli -->|"Docker Compose Local"| LocalSandbox["Contenedor Reto Local (localhost)"]

    Player -->|"HTTPS Directo"| HostedNodes["Nodos Retos Web Alojados (Docker / Railway / VPS)"]
```

### Responsabilidades por Componente

| Componente | Ubicacion | Responsabilidad |
|---|---|---|
| Portal Web `eclipsec.cl` | `CTF-Academia_cyber/EclipSec-WebPage` (Vercel) | SPA React 19 + TypeScript + Vite; interfaz corporativa y Arena CTF con `src/styles/global.css` (60-30-10), componentes genericos, Skeletons, SEO semantico, autenticacion por cookies `HttpOnly` + `X-CSRF-Token` y validacion de flags via API |
| Backend API | `academiahacking_ucncqbo/backend/` (Railway) | Logica de dominio CTF, validacion HMAC-SHA256 de flags, puntuacion atomica, ranking SQL unificado, administracion RBAC, revocacion de tokens y registro de sesiones CLI |
| Base de Datos | PostgreSQL (Railway) / SQLite (Local) | Persistencia gestionada mediante migraciones Alembic |
| Nodos de Retos Alojados | `academiahacking_ucncqbo/docker/` | Entornos web vulnerables (`web-001` a `web-011`) endurecidos con aislamiento non-root / `setpriv` y UI compartida `docker/shared/` |
| `eclipsec-cli` | `CTF-Academia_cyber/eclipsec-cli` | CLI Python (`Click`) con configuracion UTF-8 multi-SO, validacion tar/symlink segura, revocacion remota en `auth logout`, soporte de retos locales y `target_url` alojados |

---

## 2. Arquitectura Interna del Backend (Clean Code & SOLID)

```text
backend/
  alembic.ini                    Configuracion portable de migraciones
  alembic/
    env.py                       Runner Async SQLAlchemy (SQLite batch + PostgreSQL)
    versions/
      0001_initial_schema.py     Esquema inicial completo e indices compuestos
  pyproject.toml                 Configuracion de pytest, ruff y mypy
  seed.py                        Seeding idempotente e incremento seguro de catalogo
  app/
    main.py                      FastAPI, middlewares de seguridad, lifespan y /health con SELECT 1
    config.py                    Settings Pydantic con validacion fail-fast en produccion
    database.py                  Engine Async (PRAGMA foreign_keys=ON en SQLite, pool_pre_ping en PostgreSQL)
    api/
      deps.py                    Factorias DI (Depends), extraccion JWT/cookie, CSRF y throttle telemetry
      v1/
        auth.py                  Registro, sesiones HttpOnly, Bearer CLI y perfil propio
        challenges.py            Catalogo, filtros, envio de flags y start/stop CLI
        leaderboard.py           Ranking global y por pais
        users.py                 Perfil publico sin PII
        admin.py                 CRUD de retos y gestion RBAC de usuarios
        ctf_academy.py           Adaptador HTTP para contrato legado POST /api/ctf-academy
    models/                      Entidades ORM e indices compuestos
    repositories/                Interfaces Protocol e implementaciones SQLAlchemy Async
    schemas/                     Contratos Pydantic v2 con validadores y @computed_field
    services/                    Logica de aplicacion, criptografia HMAC/bcrypt y rate limiting
```

### Principios de Capas Aplicados (Fase 4)

1. **Capa de Presentacion (`backend/app/api/`)**: Los routers en `api/v1/` son delgados y no importan `sqlalchemy`; unicamente validan contratos HTTP, aplican dependencias de seguridad y delegan en los servicios inyectados por `Depends`.
2. **Capa de Aplicacion / Servicios (`backend/app/services/`)**: `AuthService`, `ChallengeService`, `LeaderboardService`, `UserService` y `CtfAcademyService` reciben interfaces `Protocol` por constructor (Inversion de Dependencias).
3. **Capa de Infraestructura (`backend/app/repositories/`, `backend/alembic/`)**: Repositorios concretos SQLAlchemy Async encapsulan las consultas, las actualizaciones atomicas contra condiciones de carrera y el manejo de `IntegrityError`, mientras Alembic versiona el esquema DDL.

---

## 3. Modelo Entidad-Relacion (Base de Datos)

```mermaid
erDiagram
    USERS ||--o{ SOLVES : "registra"
    USERS ||--o{ SUBMISSIONS : "envia"
    USERS ||--o{ CHALLENGE_INSTANCES : "inicia"
    CHALLENGES ||--o{ SOLVES : "acumula"
    CHALLENGES ||--o{ SUBMISSIONS : "recibe"
    CHALLENGES ||--o{ CHALLENGE_INSTANCES : "instancia"

    USERS {
        string id PK "UUID (36)"
        string username UK "Max 50"
        string email UK "Max 100 (normalizado lowercase)"
        string hashed_password "Bcrypt (max 72B UTF-8)"
        string role "user | admin"
        string nationality "ISO code, default CL"
        int score "Default 0"
        datetime created_at
        datetime last_connected_at
        boolean is_active
    }

    CHALLENGES {
        string id PK "UUID (36)"
        string slug UK "Max 50"
        string title "Max 100"
        text description
        string category "web, pwn, crypto, etc."
        string difficulty "EASY | MEDIUM | HARD | INSANE"
        int points
        string flag "Almacena [REDACTED]"
        string flag_hash "HMAC-SHA256 con clave de servidor"
        string target_url "Ruta relativa o URL http(s)"
        text hints
        string version "Default 1.0"
        string repository "owner/repo para CLI"
        string path "Subdirectorio en repo"
        boolean is_active
        int solves_count
        datetime created_at
        datetime updated_at
    }

    REVOKED_TOKENS {
        string jti PK "UUID (36)"
        datetime expires_at
        datetime revoked_at
    }

    SOLVES {
        string id PK "UUID (36)"
        string user_id FK
        string challenge_id FK
        int points_awarded
        datetime solved_at
    }

    SUBMISSIONS {
        string id PK "UUID (36)"
        string user_id FK
        string challenge_id FK
        string submitted_flag
        boolean is_correct
        datetime submitted_at
    }

    CHALLENGE_INSTANCES {
        string id PK "UUID (36)"
        string user_id FK
        string challenge_id FK
        string status "running | stopped | expired"
        datetime created_at
        datetime started_at
        datetime stopped_at
        datetime expiration_at
    }
```

### Restricciones e Indices Clave

- **`solves`**: Restriccion unica compuesta `uq_user_challenge_solve(user_id, challenge_id)` e indice `ix_solves_user_solved_at(user_id, solved_at)`.
- **`users`**: Indice compuesto `ix_users_active_role_score(is_active, role, score)` para acelerar ranking global y conteos.
- **`challenges`**: Indice compuesto `ix_challenges_active_category_difficulty(is_active, category, difficulty)`.
- **`submissions`**: Indice compuesto `ix_submissions_user_challenge_submitted(user_id, challenge_id, submitted_at)`.
- **`challenge_instances`**: Indice compuesto `ix_instance_user_challenge_status(user_id, challenge_id, status)`.
- **`revoked_tokens`**: Indice en `expires_at` para poda eficiente de tokens caducados.
- **Borrado en cascada**: Todas las claves foraneas hacia `users.id` y `challenges.id` utilizan `ondelete="CASCADE"`, garantizado tambien en SQLite mediante `PRAGMA foreign_keys=ON`.

---

## 4. Flujos Criticos de Secuencia

### Flujo A: Autenticacion Segura sin Exposicion de Tokens en Navegador

```mermaid
sequenceDiagram
    participant Browser as "Navegador (EclipSec-WebPage)"
    participant API as "FastAPI Backend"
    participant DB as "Base de Datos"

    Browser->>API: "POST /api/v1/auth/session/login o /api/ctf-academy (credentials: include)"
    API->>DB: "SELECT user + verify_password (bcrypt)"
    DB-->>API: "Usuario valido"
    API-->>Browser: "Set-Cookie HttpOnly (eclipsec_session) + eclipsec_csrf (sin token en JSON)"
    Browser->>API: "POST /api/v1/challenges/{slug}/submit (Cookie HttpOnly + cabecera X-CSRF-Token)"
    API-->>Browser: "FlagSubmissionResponse"
    Browser->>API: "POST /api/ctf-academy logout o /api/v1/auth/session/logout (+ X-CSRF-Token)"
    API->>DB: "INSERT revoked_tokens (jti)"
    API-->>Browser: "Clear cookies de sesion y CSRF"
```

### Flujo B: Ciclo de Vida de Retos Locales con `eclipsecCLI`

```mermaid
sequenceDiagram
    participant Player as "Jugador"
    participant CLI as "eclipsecCLI"
    participant API as "FastAPI Backend"
    participant Repo as "GitHub (CHALLENGES_REPOSITORY)"
    participant Docker as "Docker Local del Jugador"

    Player->>CLI: "eclipsec start web-sqli-001"
    CLI->>API: "POST /api/v1/challenges/web-sqli-001/start"
    API-->>CLI: "ChallengeInstanceResponse (status running, repository, path, version)"
    CLI->>Repo: "Descarga archivos de web/sqli-001"
    CLI->>Docker: "Levanta contenedor local en localhost"
    Player->>Docker: "Resuelve el reto y obtiene la flag"
    Player->>CLI: "eclipsec submit web-sqli-001"
    CLI->>API: "POST /api/v1/challenges/web-sqli-001/submit"
    API-->>CLI: "FlagSubmissionResponse (is_correct, points_awarded, new_total_score)"
    Player->>CLI: "eclipsec stop web-sqli-001"
    CLI->>API: "POST /api/v1/challenges/web-sqli-001/stop"
    API-->>CLI: "ChallengeInstanceResponse (status stopped)"
```

### Flujo C: Validacion Atomica de Flag en Tiempo Constante

1. `POST /api/v1/challenges/{slug}/submit` recupera el reto activo por `id` o `slug`.
2. Consulta `solves` para verificar si el jugador ya resolvio ese reto; si existe, retorna exito idempotente con `points_awarded = 0`.
3. Compara la flag enviada mediante `hmac.compare_digest` (tiempo constante) contra `flag_hash` (`HMAC-SHA256`).
4. Registra el intento en `submissions` almacenando su resumen `HMAC-SHA256` (nunca texto plano).
5. Si es correcta, `SqlAlchemyChallengeRepository.record_correct_solve` inserta `Solve` con `flush()`, ejecuta incrementos atomicos SQL (`Challenge.solves_count + 1` y `User.score + points`) y realiza `commit()`. Ante un `IntegrityError` concurrente en `uq_user_challenge_solve`, revierte limpiamente la transaccion y retorna resultado idempotente sin duplicar puntos.

---

## 5. Registro de Decisiones de Arquitectura (ADRs)

| ID | Decision | Estado | Justificacion |
|---|---|---|---|
| **ADR-001** | Modelo hibrido de retos: web alojados (`target_url`) + locales descargables via CLI (`repository`, `path`) | Vigente | Permite ejecutar retos pesados o sensibles en el Docker local del participante sin consumir CPU/memoria del servidor API en Railway. |
| **ADR-002** | Autenticacion web sin tokens en navegador (cookies `HttpOnly` + CSRF) separada de tokens CLI | Implementada (Fases 3 y 6) | Evita exponer JWTs en el inspector de red del navegador o en `localStorage`, mitigando robo de sesion por XSS y soportando revocacion via `revoked_tokens`. |
| **ADR-003** | Adopcion de Alembic, seeding idempotente y patron Repository con DI | Implementada (Fase 4) | Reemplaza parches DDL ad-hoc por migraciones versionadas, desacopla routers de SQLAlchemy y asegura sincronizacion incremental no destructiva de `seed.py`. |
| **ADR-004** | Aislamiento estricto por contenedor en lugar de entorno monolitico con consola root | Implementada (Fases 2 y 5) | `ttyd` y variables globales removidos en Fase 2; contenedores standalone `non-root`, `read_only`, `cap_drop: ALL`, limites de recursos y UI semantica `global.css` aplicados en Fase 5 junto a `setpriv` en monolitico. |
| **ADR-005** | Encapsulacion de `POST /api/ctf-academy` con cookies `HttpOnly` y paridad REST `v1` en frontend/CLI | Implementada (Fases 4 y 6) | `CtfAcademyService` reutiliza `AuthService`, `ChallengeService` y ranking SQL unificado mientras `EclipSec-WebPage` y `eclipsec-cli` validan flags y perfiles directamente sobre `/api/v1/*`. |
