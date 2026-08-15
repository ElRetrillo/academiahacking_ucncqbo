# EclipSec CTF - Backend API Service

Backend de alto rendimiento construido con **FastAPI**, **SQLAlchemy (Async)** y **PostgreSQL / SQLite**, diseñado para ser desplegado en **Railway** y consumido por el frontend en **Vercel** (`eclipsec.cl`).

---

## 🚀 Características Principales

1. **Gestión de Usuarios & Telemetría**:
   - Registro e inicio de sesión seguro con JWT (Argon2 / Bcrypt).
   - **Nacionalidad** (`nationality`): Código de país (ej. `CL`, `AR`, `PE`, `MX`, `ES`) con banderas en el ranking.
   - **Puntaje** (`score`): Suma acumulada de puntos de retos resueltos.
   - **Fecha de Inicio** (`created_at`): Registro de cuándo el jugador se unió a la plataforma.
   - **Último Momento Conectado** (`last_connected_at`): Actualización automática en cada solicitud autenticada.

2. **Mecanismo de Retos & Flags**:
   - Listado público con indicador de resolución dinámica (`is_solved: true/false`).
   - Verificación de flags en **tiempo constante** (`hmac.compare_digest`) para mitigar ataques de temporización (timing attacks).
   - Prevención estricta de resoluciones duplicadas (no otorga puntos repetidos).
   - Registro histórico de envíos (`submissions`) y resoluciones (`solves`).

3. **Leaderboard en Tiempo Real**:
   - Ranking global ordenado por:
     1. Mayor puntaje (`score DESC`).
     2. Menor tiempo de resolución en el último reto resuelto (criterio de desempate).
     3. Fecha de inicio (`created_at ASC`).
   - Métricas agregadas por país (`/api/v1/leaderboard/countries`).

4. **Panel de Administración (RBAC)**:
   - Endpoints protegidos con rol `admin`.
   - Creación, actualización y eliminación de retos con asignación de dificultad (`EASY`, `MEDIUM`, `HARD`, `INSANE`), puntajes y flags.
   - Gestión de usuarios (cambio de roles, ajuste de puntuaciones, activación/suspensión).

5. **Integración con Vercel**:
   - Soporte nativo de CORS para `https://eclipsec.cl` y cualquier subdominio preview `https://*.vercel.app`.
   - Documentación Swagger interactiva lista en `/docs`.

---

## 📡 Referencia de la API

### Autenticación (`/api/v1/auth`)
| Método | Endpoint | Descripción | Auth Requerida |
|---|---|---|---|
| `POST` | `/api/v1/auth/register` | Registrar nuevo jugador (`username`, `email`, `password`, `nationality`) | No |
| `POST` | `/api/v1/auth/login` | Iniciar sesión y obtener token JWT Bearer | No |
| `GET` | `/api/v1/auth/me` | Obtener perfil del usuario actual, estadísticas y solves | Sí (Bearer) |
| `PUT` | `/api/v1/auth/me` | Actualizar nacionalidad o contraseña | Sí (Bearer) |

### Retos (`/api/v1/challenges`)
| Método | Endpoint | Descripción | Auth Requerida |
|---|---|---|---|
| `GET` | `/api/v1/challenges` | Listar todos los retos activos (indica `is_solved` si se envía token) | Opcional |
| `GET` | `/api/v1/challenges/{id_or_slug}` | Obtener detalle de un reto específico | Opcional |
| `POST` | `/api/v1/challenges/{id_or_slug}/submit` | Enviar una flag para validación y suma de puntos | Sí (Bearer) |

### Ranking & Leaderboard (`/api/v1/leaderboard`)
| Método | Endpoint | Descripción | Auth Requerida |
|---|---|---|---|
| `GET` | `/api/v1/leaderboard` | Tabla de clasificación general con ranks, puntajes, fechas y países | No |
| `GET` | `/api/v1/leaderboard/countries` | Estadísticas agrupadas por nacionalidad | No |

### Panel de Administración (`/api/v1/admin`)
| Método | Endpoint | Descripción | Auth Requerida |
|---|---|---|---|
| `GET` | `/api/v1/admin/challenges` | Listar todos los retos con flags y soluciones | Admin |
| `POST` | `/api/v1/admin/challenges` | Crear nuevo reto (`title`, `slug`, `points`, `difficulty`, `flag`) | Admin |
| `PUT` | `/api/v1/admin/challenges/{id}` | Editar reto, dificultad, puntos o flag | Admin |
| `DELETE` | `/api/v1/admin/challenges/{id}` | Eliminar reto | Admin |
| `GET` | `/api/v1/admin/users` | Listar todos los usuarios, roles y telemetría | Admin |
| `PUT` | `/api/v1/admin/users/{id}` | Modificar rol (`user`/`admin`), estado o puntaje | Admin |

---

## 🛠️ Ejecución Local

### 1. Requisitos
- Python 3.11+
- Virtualenv

### 2. Instalación
```bash
# Crear entorno virtual e instalar dependencias
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Poblar base de datos inicial con 11 retos y usuarios demo
python seed.py

# Iniciar servidor de desarrollo
uvicorn app.main:app --reload --port 8000
```
Visita `http://localhost:8000/docs` para ver la interfaz Swagger.

---

## 🚢 Despliegue en Railway

1. **Crear Proyecto en Railway**:
   - Conecta el repositorio de GitHub.
   - Agrega un plugin de **PostgreSQL** al proyecto en Railway.
2. **Configurar el Servicio Backend**:
   - **Root Directory**: `backend` (o raíz con el `Dockerfile` apuntando a `backend/Dockerfile`).
   - Railway inyectará automáticamente `DATABASE_URL` y `PORT`.
3. **Variables de Entorno (Environment Variables)**:
   ```env
   ENVIRONMENT=production
   JWT_SECRET=tu-clave-secreta-super-larga-y-aleatoria
   CORS_ORIGINS=https://eclipsec.cl,https://www.eclipsec.cl,http://localhost:3000
   ADMIN_USERNAME=admin
   ADMIN_EMAIL=admin@eclipsec.cl
   ADMIN_PASSWORD=ContraseñaSuperSeguraAdmin2026!
   ```

---

## 💻 Conexión desde el Frontend en Vercel (TypeScript / Next.js)

Ejemplo de cliente API para tu proyecto `eclipsec`:

```typescript
// lib/api.ts
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://tu-backend.up.railway.app';

export async function fetchWithAuth(endpoint: string, options: RequestInit = {}) {
  const token = localStorage.getItem('token');
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  };

  const response = await fetch(`${API_URL}${endpoint}`, { ...options, headers });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Error en la petición');
  }
  return response.json();
}

// 1. Obtener Lista de Retos
export const getChallenges = () => fetchWithAuth('/api/v1/challenges');

// 2. Enviar Flag
export const submitFlag = (challengeSlug: string, flag: string) =>
  fetchWithAuth(`/api/v1/challenges/${challengeSlug}/submit`, {
    method: 'POST',
    body: JSON.stringify({ flag }),
  });

// 3. Obtener Leaderboard
export const getLeaderboard = () => fetchWithAuth('/api/v1/leaderboard');

// 4. Obtener Métricas por País
export const getCountryStats = () => fetchWithAuth('/api/v1/leaderboard/countries');
```
