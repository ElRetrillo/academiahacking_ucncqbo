# Referencia Oficial de la API (EclipSec CTF)

**Base URL (Local):** `http://localhost:8000`
**Documentacion OpenAPI Interactiva:** `/docs` (Swagger UI) y `/redoc` (ReDoc)
**Estado del Contrato:** Documentacion fiel al codigo vigente en `backend/app/api/v1/`, incluyendo notas de migracion de seguridad hacia la Fase 3.

---

## 1. Convenciones Generales y Seguridad de Integracion

### Regla de Integracion Segura para Navegadores

En el estado actual del backend, los endpoints protegidos de `/api/v1/*` aceptan autenticacion mediante cabecera `Authorization: Bearer <jwt>`. No obstante, conforme al estandar definido en [STANDARDS.md](./STANDARDS.md):

- **En navegador web (`eclipsec.cl`)**: El codigo cliente JavaScript **nunca** debe almacenar el JWT en `localStorage` ni enviar el token directamente en vistas de red desde el navegador. El frontend Next.js debe operar como un **BFF (Backend for Frontend)** en servidor (Route Handlers / Server Actions) o recibir sesion mediante cookies `HttpOnly; Secure; SameSite=Lax` (a habilitar en Fase 3).
- **En terminal (`eclipsecCLI`)**: Puede utilizar autenticacion Bearer desde consola hacia los endpoints de retos e instancias.

### Formatos y Codigos de Estado

- Content-Type de entrada y salida: `application/json` (UTF-8).
- Fechas en formato ISO 8601 con zona horaria UTC (en `/api/ctf-academy` las fechas se serializan como epoch en milisegundos).
- Errores estandar FastAPI (`400`, `401`, `403`, `404`, `422`): `{"detail": "Mensaje descriptivo"}`.

---

## 2. Salud del Servicio

| Metodo | Ruta | Autenticacion | Descripcion |
|---|---|---|---|
| `GET` | `/` | No | Verificacion basica de estado |
| `GET` | `/health` | No | Healthcheck configurado para Railway |

Respuesta `200 OK`:
```json
{
  "status": "ok"
}
```

---

## 3. Autenticacion (`/api/v1/auth`)

### `POST /api/v1/auth/register`
Registra una nueva cuenta de jugador y devuelve su perfil inicial.

- **Body (`RegisterRequest`)**:
  - `username`: string (3-50 caracteres, regex `^[a-zA-Z0-9_-]+$`)
  - `email`: EmailStr
  - `password`: string (6-100 caracteres)
  - `nationality`: string (2-10 caracteres, default `"CL"`)
- **Respuesta `201 Created` (`UserProfile`)**:
```json
{
  "id": "uuid",
  "username": "jugador_ucn",
  "email": "jugador@eclipsec.cl",
  "nationality": "CL",
  "role": "user",
  "score": 0,
  "created_at": "2026-11-20T14:00:00Z",
  "last_connected_at": "2026-11-20T14:00:00Z",
  "is_active": true,
  "solves_count": 0
}
```
- **Nota de auditoria (SEC-04):** Actualmente, si la tabla `users` esta vacia, el primer usuario registrado recibe `role: "admin"`. Este comportamiento sera eliminado en Fase 3.

### `POST /api/v1/auth/login`
Autentica por `username` o `email` y retorna `TokenResponse`.

- **Body (`LoginRequest`)**: `{"username_or_email": "...", "password": "..."}`
- **Respuesta `200 OK` (`TokenResponse`)**: `{"access_token": "<token>", "token_type": "bearer", "user": { ... }}`
- **Uso esperado:** Consumido desde servidor BFF (portal web) o desde `eclipsecCLI`.

### `GET /api/v1/auth/me`
- **Autenticacion:** Requerida (`Bearer`).
- **Respuesta `200 OK` (`UserProfileDetail`)**: Perfil completo del jugador autenticado, incluyendo estadisticas, rango, conteo por categoria y ultimos 10 retos resueltos.

### `PUT /api/v1/auth/me`
- **Autenticacion:** Requerida (`Bearer`).
- **Body (`UserUpdate`)**: `nationality` (opcional), `current_password` (requerida si cambia password), `new_password` (opcional, 6-100 caracteres).
- **Respuesta `200 OK` (`UserProfile`)**.

---

## 4. Retos CTF e Instancias (`/api/v1/challenges`)

### `GET /api/v1/challenges`
Lista todos los retos activos ordenados por `points ASC, slug ASC`.
- **Query params opcionales:** `category`, `difficulty` (`EASY`, `MEDIUM`, `HARD`, `INSANE`).
- **Autenticacion:** Opcional. Si hay sesion valida, marca `is_solved: true/false` para el jugador actual.
- **Resolucion de `target_url`**: Si el valor guardado es relativo (ej. `/web-001/`) y `CHALLENGES_BASE_URL` esta configurado, devuelve la URL absoluta. Nunca expone el campo `flag`.

### `GET /api/v1/challenges/recent`
Retorna los retos activos mas recientes (`limit` entre 1 y 20, default `5`).

### `GET /api/v1/challenges/categories`
Retorna el resumen de categorias activas y cantidad de retos disponibles:
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
- **Autenticacion:** Requerida (`Bearer`).
- **Body (`FlagSubmissionRequest`)**: `{"flag": "EclipSec{...}"}`
- **Comportamiento:** Verifica la flag en tiempo constante (`hmac.compare_digest`), registra el intento en `submissions` y evita doble puntuacion si el reto ya fue resuelto por el jugador.
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
- **Autenticacion:** Requerida (`Bearer`).
- **Descripcion:** Inicia (o retorna de forma idempotente si ya existe una sesion `running`) un registro `ChallengeInstance` con los metadatos necesarios para que `eclipsecCLI` descargue y ejecute el reto localmente. El backend nunca ejecuta contenedores Docker.
- **Respuesta `200 OK` (`ChallengeInstanceResponse`)**:
```json
{
  "id": "uuid",
  "status": "running",
  "created_at": "2026-11-20T14:00:00Z",
  "started_at": "2026-11-20T14:00:00Z",
  "stopped_at": null,
  "expiration_at": null,
  "challenge": {
    "id": "uuid",
    "slug": "web-sqli-001",
    "title": "Login Bypass",
    "category": "web",
    "difficulty": "EASY",
    "points": 100,
    "version": "1.0",
    "repository": "ElRetrillo/retos_ctf",
    "path": "web/sqli-001",
    "target_url": null
  }
}
```

### `POST /api/v1/challenges/{challenge_id_or_slug}/stop`
- **Autenticacion:** Requerida (`Bearer`).
- **Descripcion:** Marca la instancia activa (`running`) del jugador para ese reto como `stopped` y registra `stopped_at`. Retorna `404` si no existe instancia activa.

---

## 5. Leaderboard y Perfiles (`/api/v1/leaderboard`, `/api/v1/users`)

### `GET /api/v1/leaderboard`
- **Query param:** `limit` (1 a 500, default `100`).
- **Criterios de ordenamiento:**
  1. `score DESC`
  2. `last_solve_at ASC NULLS LAST` (quien alcanzo primero el puntaje gana el desempate)
  3. `created_at ASC`
- Solo incluye cuentas activas con `role == "user"`.

### `GET /api/v1/leaderboard/countries`
Retorna metricas agregadas por `nationality` (`total_players`, `total_score`, `total_solves`), ordenadas por puntaje total y resoluciones totales descendentes.

### `GET /api/v1/users/{username}/profile`
Retorna `UserProfileDetail` con rango calculado segun puntaje:
- `0`: `Noob`
- `< 500`: `Script Kiddie`
- `< 1000`: `Hacker`
- `< 2000`: `Pro Hacker`
- `< 4000`: `Elite Hacker`
- `< 8000`: `Guru`
- `>= 8000`: `Omniscient`

- **Nota de auditoria (SEC-07):** Este endpoint actualmente no exige autenticacion y expone `email`, `role` y `is_active`. En Fase 3 dichos campos seran removidos de la vista publica.

---

## 6. Panel de Administracion (`/api/v1/admin`)

Todos los endpoints requieren usuario autenticado con `role == "admin"` (responden `403 Forbidden` en caso contrario).

| Metodo | Ruta | Descripcion |
|---|---|---|
| `GET` | `/api/v1/admin/challenges` | Lista todos los retos incluyendo campos internos (`flag`, `is_active`, `created_at`) |
| `POST` | `/api/v1/admin/challenges` | Crea un reto (`ChallengeCreate`) |
| `PUT` | `/api/v1/admin/challenges/{challenge_id}` | Actualiza campos de un reto (`ChallengeUpdate`) |
| `DELETE` | `/api/v1/admin/challenges/{challenge_id}` | Elimina un reto (`204 No Content`) |
| `GET` | `/api/v1/admin/users` | Lista todos los usuarios registrados con su `solves_count` |
| `PUT` | `/api/v1/admin/users/{user_id}` | Actualiza `role`, `is_active`, `nationality` o `score` de un usuario |

---

## 7. Adaptador Legacy (`POST /api/ctf-academy`)

Mantiene compatibilidad con el contrato RPC historico del frontend mediante un cuerpo JSON `{ "action": "...", ... }`:

| Accion | Parametros | Comportamiento Vigente |
|---|---|---|
| `register` | `username`, `password` | Crea usuario con correo sintetico `<username>@ctf.eclipsec.cl` y retorna estado de academia |
| `login` | `username`, `password` | Autentica y retorna estado de academia |
| `logout` | Ninguno | Responde `ok: true` (sin revocacion de sesion en servidor actualmente) |
| `state` | Header `Authorization` opcional | Retorna `leaderboard` (top 50), `participants`, `currentUser` y `session` |
| `complete` | `challengeId`, `flag` (Auth requerido) | Valida flag y retorna estado actualizado |

Este endpoint se encuentra marcado para migracion controlada hacia los recursos REST `/api/v1/*` tras habilitar la capa BFF del portal web.

---

## 8. Patron de Cliente Seguro para Frontend Next.js (BFF)

Ejemplo de cliente del lado del servidor Next.js (Route Handler / Server Action) donde las credenciales y tokens se procesan exclusivamente en el backend de Vercel y nunca se exponen en `localStorage` ni en respuestas hacia el navegador:

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

Desde los componentes React del navegador, los formularios y acciones solo llaman a rutas internas del propio frontend (`/api/session/login`, `/api/challenges`), las cuales gestionan la cookie `HttpOnly` sin exponer tokens en vistas de red ni en almacenamiento del navegador.
