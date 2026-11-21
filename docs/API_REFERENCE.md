# Referencia Oficial de la API (EclipSec CTF)

**Base URL (Local):** `http://localhost:8000`
**Documentacion OpenAPI Interactiva:** `/docs` (Swagger UI) y `/redoc` (ReDoc)
**Estado del Contrato:** Documentacion actualizada tras el endurecimiento DevSecOps y refactorizacion SOLID de Fases 3 y 4 en `backend/app/api/v1/`.

---

## 1. Convenciones Generales y Seguridad de Integracion

### Regla de Integracion Segura para Navegadores

- **Navegador web (`eclipsec.cl`)**: Debe utilizar `POST /api/v1/auth/session/login` (que emite cookie `HttpOnly` + cookie CSRF `eclipsec_csrf` sin tokens en el cuerpo JSON) o operar detras de un **BFF (Backend for Frontend)** en Next.js. En peticiones mutadoras (`POST`, `PUT`, `PATCH`, `DELETE`) autenticadas por cookie se exige la cabecera `X-CSRF-Token` coincidente con la cookie `eclipsec_csrf`.
- **Terminal (`eclipsecCLI`) y BFF server-side**: Utilizan `POST /api/v1/auth/login` obteniendo un token Bearer acotado (`typ="cli"`).

### Formatos y Codigos de Estado

- Content-Type de entrada y salida: `application/json` (UTF-8).
- Fechas en formato ISO 8601 UTC (en `/api/ctf-academy` se serializan como epoch UTC en milisegundos).
- Errores estandar FastAPI (`400`, `401`, `403`, `404`, `422`, `429`, `503`): `{"detail": "Mensaje descriptivo"}`.
- Limite de tasa (`429 Too Many Requests`): Incluye cabecera `Retry-After` en segundos en endpoints de autenticacion y envio de flags, usando identificacion resistente a spoofing via `TRUSTED_PROXY_COUNT`.

---

## 2. Salud del Servicio

| Metodo | Ruta | Autenticacion | Descripcion |
|---|---|---|---|
| `GET` | `/` | No | Verificacion basica de proceso HTTP (`{"status": "ok"}`) |
| `GET` | `/health` | No | Healthcheck con prueba real `SELECT 1` contra base de datos para Railway |

Respuesta `GET /health` (`200 OK`):
```json
{
  "status": "ok",
  "database": "ok"
}
```

Respuesta ante indisponibilidad de base de datos (`503 Service Unavailable`):
```json
{
  "status": "degraded",
  "database": "error"
}
```

---

## 3. Autenticacion (`/api/v1/auth`)

### `POST /api/v1/auth/register`
Registra una nueva cuenta de jugador (`role: "user"` por defecto; normaliza `email` a minusculas y `nationality` a mayusculas). Sujeto a rate limiting.

- **Body (`RegisterRequest`)**:
  - `username`: string (3-50 caracteres, regex `^[a-zA-Z0-9_-]+$`)
  - `email`: EmailStr (unico case-insensitive)
  - `password`: string (minimo 6 caracteres, maximo 72 bytes UTF-8 por limite criptografico de bcrypt)
  - `nationality`: string (2-10 caracteres, default `"CL"`)
- **Respuesta `201 Created` (`UserProfile`)**:
```json
{
  "id": "uuid",
  "username": "jugador_ucn",
  "email": "jugador@example.com",
  "nationality": "CL",
  "role": "user",
  "score": 0,
  "created_at": "2026-11-20T14:00:00Z",
  "last_connected_at": "2026-11-20T14:00:00Z",
  "is_active": true,
  "solves_count": 0
}
```

### `POST /api/v1/auth/login`
Autentica por `username` o `email` (case-insensitive en email) y retorna `TokenResponse` (`typ="cli"`) para `eclipsecCLI` o servidor BFF. Sujeto a rate limiting.

- **Body (`LoginRequest`)**: `{"username_or_email": "...", "password": "..."}`
- **Respuesta `200 OK` (`TokenResponse`)**: `{"access_token": "<token>", "token_type": "bearer", "user": { ... }}`

### `POST /api/v1/auth/session/login`
Autentica una sesion web emitiendo cookie `HttpOnly` (`eclipsec_session`) y cookie CSRF (`eclipsec_csrf`) sin exponer ningun token en el cuerpo JSON. Sujeto a rate limiting.

- **Body (`LoginRequest`)**: `{"username_or_email": "...", "password": "..."}`
- **Respuesta `200 OK` (`SessionResponse`)**:
```json
{
  "authenticated": true,
  "user": {
    "id": "uuid",
    "username": "jugador_ucn",
    "email": "jugador@example.com",
    "nationality": "CL",
    "role": "user",
    "score": 0,
    "created_at": "2026-11-20T14:00:00Z",
    "last_connected_at": "2026-11-20T14:00:00Z",
    "is_active": true,
    "solves_count": 0
  }
}
```

### `POST /api/v1/auth/session/logout` y `POST /api/v1/auth/logout`
Revoca el `jti` del token activo en `revoked_tokens`, poda registros expirados y elimina las cookies de sesion/CSRF. Si autentica mediante cookie, exige cabecera `X-CSRF-Token`.

- **Respuesta `200 OK` (`LogoutResponse`)**: `{"authenticated": false, "message": "Session closed."}`

### `GET /api/v1/auth/me`
- **Autenticacion:** Requerida (cookie `HttpOnly` o `Bearer`).
- **Respuesta `200 OK` (`UserProfileDetail`)**: Perfil privado completo del jugador autenticado, incluyendo `email`, `role`, `last_connected_at`, estadisticas, rango unificado y ultimos 10 retos resueltos (con campos `snake_case` y `camelCase` via `@computed_field`).

### `PUT /api/v1/auth/me`
- **Autenticacion:** Requerida (cookie `HttpOnly` + `X-CSRF-Token`, o `Bearer`).
- **Body (`UserUpdate`)**: `nationality` (opcional), `current_password` (requerida si cambia password), `new_password` (opcional, minimo 6 caracteres y maximo 72 bytes UTF-8).
- **Respuesta `200 OK` (`UserProfile`)**.

---

## 4. Retos CTF e Instancias (`/api/v1/challenges`)

### `GET /api/v1/challenges`
Lista todos los retos activos ordenados por `points ASC, slug ASC`.
- **Query params opcionales:** `category`, `difficulty` (`EASY`, `MEDIUM`, `HARD`, `INSANE`).
- **Autenticacion:** Opcional. Marca `is_solved: true/false` para el jugador actual.
- **Resolucion de `target_url`**: Si es relativa y `CHALLENGES_BASE_URL` esta configurado, devuelve la URL absoluta. Nunca expone el campo `flag`.

### `GET /api/v1/challenges/recent`
Retorna los retos activos mas recientes (`limit` entre 1 y 20, default `5`).

### `GET /api/v1/challenges/categories`
Retorna categorias activas y cantidad de retos disponibles:
```json
[
  {
    "category": "web",
    "count": 12
  }
]
```

### `GET /api/v1/challenges/{challenge_id_or_slug}`
Obtiene el detalle publico (`ChallengePublic`) de un reto activo buscando por UUID o `slug`. Incluye metadatos CLI (`version`, `repository`, `path`) cuando corresponden a retos locales.

### `POST /api/v1/challenges/{challenge_id_or_slug}/submit`
- **Autenticacion:** Requerida (cookie `HttpOnly` + `X-CSRF-Token`, o `Bearer`). Sujeto a rate limiting (`429` + `Retry-After`).
- **Body (`FlagSubmissionRequest`)**: `{"flag": "EclipSec{...}"}`
- **Comportamiento:** Verifica la flag en tiempo constante contra su resumen `HMAC-SHA256`, registra el hash del intento en `submissions` (nunca en texto plano) y actualiza `solves_count` y `score` con incrementos atomicos SQL protegidos ante envios concurrentes.
- **Respuesta `200 OK` (`FlagSubmissionResponse`)**:
```json
{
  "is_correct": true,
  "message": "Congratulations! Flag accepted (+100 pts)",
  "points_awarded": 100,
  "new_total_score": 250
}
```

### `POST /api/v1/challenges/{challenge_id_or_slug}/start`
- **Autenticacion:** Requerida (cookie `HttpOnly` + `X-CSRF-Token`, o `Bearer`).
- **Descripcion:** Inicia (o retorna de forma idempotente si ya existe una sesion `running`) un registro `ChallengeInstance` con los metadatos necesarios para que `eclipsecCLI` descargue y ejecute el reto localmente.

### `POST /api/v1/challenges/{challenge_id_or_slug}/stop`
- **Autenticacion:** Requerida (cookie `HttpOnly` + `X-CSRF-Token`, o `Bearer`).
- **Descripcion:** Marca la instancia activa (`running`) del jugador como `stopped`. Retorna `404` si no existe instancia activa.

---

## 5. Leaderboard y Perfiles (`/api/v1/leaderboard`, `/api/v1/users`)

### `GET /api/v1/leaderboard`
- **Query param:** `limit` (1 a 500, default `100`).
- **Criterios de ordenamiento:** `score DESC`, `last_solve_at ASC NULLS LAST`, `created_at ASC`, `id ASC`. Solo incluye cuentas activas con `role == "user"`.

### `GET /api/v1/leaderboard/countries`
Retorna metricas agregadas por `nationality` (`total_players`, `total_score`, `total_solves`).

### `GET /api/v1/users/{username}/profile`
Retorna `UserPublicProfileDetail` (sin `email`, `role`, `is_active` ni `last_connected_at`) con `global_rank` consistente con `/api/v1/leaderboard` y rango calculado segun puntaje (`Noob`, `Script Kiddie`, `Hacker`, `Pro Hacker`, `Elite Hacker`, `Guru`, `Omniscient`).

---

## 6. Panel de Administracion (`/api/v1/admin`)

Todos los endpoints requieren usuario autenticado con `role == "admin"` (responden `403 Forbidden` en caso contrario).

| Metodo | Ruta | Descripcion |
|---|---|---|
| `GET` | `/api/v1/admin/challenges` | Lista todos los retos con `flag: "[REDACTED]"` y `flag_configured: bool` |
| `POST` | `/api/v1/admin/challenges` | Crea un reto validando `difficulty`, `category`, `target_url` segura (`/` o `http(s)`), `path` sin `..` y `flag` valida (`HMAC-SHA256`) |
| `PUT` | `/api/v1/admin/challenges/{challenge_id}` | Actualiza campos o rota el hash de flag (`ChallengeUpdate`) |
| `DELETE` | `/api/v1/admin/challenges/{challenge_id}` | Elimina un reto y sus relaciones en cascada (`204 No Content`) |
| `GET` | `/api/v1/admin/users` | Lista todos los usuarios registrados con su `solves_count` |
| `PUT` | `/api/v1/admin/users/{user_id}` | Actualiza `role` (`user`/`admin`), `is_active`, `nationality` o `score >= 0` (bloquea auto-desactivacion o auto-degradacion del admin autenticado) |

---

## 7. Adaptador Legacy (`POST /api/ctf-academy`)

Mantiene compatibilidad con el contrato RPC historico mediante `{ "action": "...", ... }`, respaldado por `CtfAcademyService` con cookies `HttpOnly` + CSRF, rate limiting, revocacion real de `jti`, ranking SQL unificado y timestamps UTC en milisegundos:

| Accion | Parametros | Comportamiento Vigente |
|---|---|---|
| `register` | `username`, `password` (min 6, max 72B) | Registra cuenta (`role: "user"`), emite cookies `HttpOnly` + CSRF y retorna estado sin `token` en JSON |
| `login` | `username`, `password` | Autentica de forma segura sin 500 por longitud, emite cookies `HttpOnly` + CSRF y retorna estado sin `token` en JSON |
| `logout` | Cookie / Bearer (+ `X-CSRF-Token`) | Revoca `jti` en `revoked_tokens` y limpia cookies |
| `state` | Cookie o `Authorization` opcional | Retorna `leaderboard` (top 50), `participants`, `currentUser` y `session` |
| `complete` | `challengeId`, `flag` (+ `X-CSRF-Token` en cookie) | Valida flag con HMAC y retorna estado actualizado |

Este endpoint permanece programado para retiro controlado tras completar la integracion del frontend en Fase 6.

---

## 8. Patron de Cliente Seguro para Frontend Web (`HttpOnly` + CSRF / BFF)

En `EclipSec-WebPage/src/lib/api.ts`, el cliente browser autentica mediante cookies `HttpOnly` (`credentials: 'include'`) e inyecta automaticamente la cabecera `X-CSRF-Token` leida desde `eclipsec_csrf` en peticiones mutadoras (`POST`, `PUT`, `PATCH`, `DELETE`), eliminando cualquier token JWT en `localStorage` o cabeceras `Authorization: Bearer`.

Para arquitecturas con proxy SSR (ej. Next.js Route Handlers / Server Actions), puede utilizarse adicionalmente un servidor BFF:

```typescript
import { cookies } from 'next/headers';

const BACKEND_URL = process.env.CTF_API_INTERNAL_URL || 'http://localhost:8000';
const SESSION_COOKIE = 'eclipsec_session';

export async function backendServerFetch<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const cookieStore = await cookies();
  const sessionToken = cookieStore.get(SESSION_COOKIE)?.value;

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(sessionToken ? { Authorization: `Bearer ${sessionToken}` } : {}),
    ...options.headers,
  };

  const response = await fetch(`${BACKEND_URL}${endpoint}`, {
    ...options,
    headers,
    cache: 'no-store',
  });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(errorBody.detail || `HTTP ${response.status}`);
  }

  if (response.status === 204) {
    return {} as T;
  }

  return response.json() as Promise<T>;
}
```
