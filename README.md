# Academia de Hacking Competitivo UCN Coquimbo (CTF Backend & Challenges)

Plataforma y motor backend de retos CTF desarrollado por estudiantes del minor de Ciberseguridad en conjunto con la Escuela de Ingeniería de la Universidad Católica del Norte (Coquimbo), diseñado para conectarse con la plataforma web principal **EclipSec** alojada en Vercel (`eclipsec.cl`).

---

## 📌 Resumen de Cambios Recientes

Se implementó la arquitectura completa del backend en [`/backend`](file:///home/daniel/academiahacking_ucncqbo/backend):

1. **Autenticación & Telemetría:**
   - Registro y login JWT (Bcrypt + Argon2).
   - Control de jugadores con atributos requeridos: `nationality` (código de país/bandera), `score` (puntuación acumulada), `created_at` (fecha de inicio) y `last_connected_at` (telemetría en vivo actualizada en cada solicitud).
2. **Mecanismo de Retos & Flags:**
   - Validación de flags en **tiempo constante** (`hmac.compare_digest`) anti timing-attacks.
   - Prevención estricta de doble puntuación (solves únicos por usuario/reto).
   - Historial de envíos (`submissions`) y resoluciones (`solves`).
3. **Leaderboard & Estadísticas por País:**
   - Ranking global en tiempo real ordenado por puntaje y desempate por fecha del último solve.
   - Endpoint dedicado de métricas agregadas por nacionalidad (`/api/v1/leaderboard/countries`).
4. **Panel de Administración (RBAC):**
   - Endpoints para gestión total de retos (creación, dificultad, puntajes, flags) y usuarios (cambio de roles, ajuste de puntuaciones, activación/suspensión).
5. **Poblado Automático (`seed.py`):**
   - Importación de los 11 retos de la plataforma con sus respectivas flags y un usuario admin inicial.
6. **Soporte Railway & Vercel:**
   - `Dockerfile` y `railway.json` listos para producción con PostgreSQL.
   - Middleware CORS adaptado para `https://eclipsec.cl` y cualquier preview `https://*.vercel.app`.

---

## 🔌 Guía de Integración con el Frontend en Vercel (EclipSec)

### 1. Variables de Entorno en Vercel

En el panel de tu proyecto en **Vercel** (`Settings > Environment Variables`), agrega:

```env
NEXT_PUBLIC_API_URL=https://tu-backend-railway.up.railway.app
```

---

### 2. Cliente de API en el Frontend (`lib/api.ts` o `services/api.ts`)

Crea un helper para manejar las peticiones HTTP y la inyección automática del token JWT:

```typescript
// lib/api.ts
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = typeof window !== 'undefined' ? localStorage.getItem('eclipsec_token') : null;

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  };

  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({ detail: 'Error en la petición' }));
    throw new Error(errorBody.detail || `Error HTTP ${response.status}`);
  }

  // Si la respuesta es 204 No Content
  if (response.status === 204) return {} as T;

  return response.json();
}
```

---

### 3. Módulo de Autenticación (`services/auth.ts`)

Implementa las funciones de registro, login y obtención de perfil:

```typescript
// services/auth.ts
import { apiRequest } from '@/lib/api';

export interface UserProfile {
  id: string;
  username: string;
  email: string;
  nationality: string; // ej: "CL", "AR", "PE"
  role: 'user' | 'admin';
  score: number;
  created_at: string;        // Fecha inicio
  last_connected_at: string; // Último momento conectado
  is_active: boolean;
  solves_count: number;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: UserProfile;
}

// 1. Registro
export async function register(data: {
  username: string;
  email: string;
  password: string;
  nationality: string;
}) {
  return apiRequest<UserProfile>('/api/v1/auth/register', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

// 2. Inicio de Sesión
export async function login(credentials: {
  username_or_email: string;
  password: string;
}): Promise<AuthResponse> {
  const data = await apiRequest<AuthResponse>('/api/v1/auth/login', {
    method: 'POST',
    body: JSON.stringify(credentials),
  });

  if (typeof window !== 'undefined' && data.access_token) {
    localStorage.setItem('eclipsec_token', data.access_token);
    localStorage.setItem('eclipsec_user', JSON.stringify(data.user));
  }

  return data;
}

// 3. Obtener Usuario Actual (Mantiene viva la telemetría last_connected_at)
export async function getMe(): Promise<UserProfile> {
  return apiRequest<UserProfile>('/api/v1/auth/me');
}

// 4. Cerrar Sesión
export function logout() {
  if (typeof window !== 'undefined') {
    localStorage.removeItem('eclipsec_token');
    localStorage.removeItem('eclipsec_user');
  }
}
```

---

### 4. Módulo de Retos y Envío de Flags (`services/challenges.ts`)

```typescript
// services/challenges.ts
import { apiRequest } from '@/lib/api';

export interface Challenge {
  id: string;
  slug: string;
  title: string;
  description: string;
  category: string;
  difficulty: 'EASY' | 'MEDIUM' | 'HARD' | 'INSANE';
  points: number;
  target_url?: string;
  hints?: string;
  solves_count: number;
  is_solved: boolean; // Si el token está presente, indica si el usuario ya lo resolvió
}

export interface FlagSubmitResult {
  is_correct: boolean;
  message: string;
  points_awarded: number;
  new_total_score: number;
}

// Listar retos (reconoce usuario logueado automáticamente)
export async function getChallenges(): Promise<Challenge[]> {
  return apiRequest<Challenge[]>('/api/v1/challenges');
}

// Enviar Flag
export async function submitFlag(slug: string, flag: string): Promise<FlagSubmitResult> {
  return apiRequest<FlagSubmitResult>(`/api/v1/challenges/${slug}/submit`, {
    method: 'POST',
    body: JSON.stringify({ flag }),
  });
}
```

---

### 5. Módulo del Leaderboard (`services/leaderboard.ts`)

```typescript
// services/leaderboard.ts
import { apiRequest } from '@/lib/api';

export interface LeaderboardEntry {
  rank: number;
  user_id: string;
  username: string;
  nationality: string;
  score: number;
  solves_count: number;
  start_date: string;
  last_connected_at: string;
  last_solve_at?: string;
}

export interface LeaderboardResponse {
  total_players: number;
  leaderboard: LeaderboardEntry[];
}

export async function getLeaderboard(limit = 100): Promise<LeaderboardResponse> {
  return apiRequest<LeaderboardResponse>(`/api/v1/leaderboard?limit=${limit}`);
}

export async function getCountryStats() {
  return apiRequest<Array<{
    nationality: string;
    total_players: number;
    total_score: number;
    total_solves: number;
  }>>('/api/v1/leaderboard/countries');
}
```

---

## 🛠️ Despliegue en Railway (Paso a Paso)

1. En tu proyecto de **Railway**, haz clic en **New > Database > PostgreSQL**.
2. Haz clic en **New > GitHub Repo** y selecciona este repositorio (`academiahacking_ucncqbo`).
3. En la configuración del servicio:
   - **Root Directory**: Deja vacío o `/` (Railway usará automáticamente `backend/Dockerfile` vía `railway.json`).
4. Configura las siguientes **Variables de Entorno**:
   - `ENVIRONMENT` = `production`
   - `JWT_SECRET` = `(Cadena aleatoria de 32+ caracteres)`
   - `CORS_ORIGINS` = `https://eclipsec.cl,https://www.eclipsec.cl,http://localhost:3000`
   - `ADMIN_USERNAME` = `admin`
   - `ADMIN_EMAIL` = `admin@eclipsec.cl`
   - `ADMIN_PASSWORD` = `(TuContraseñaSeguraDeAdmin)`
5. Railway desplegará el contenedor, ejecutará el `seed.py` inicial (creando retos y admin) y levantará la API en el puerto dinámico `$PORT`.
