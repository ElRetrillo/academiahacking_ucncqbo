# Estandares de Ingenieria, Seguridad y Diseno (Entorno CTF EclipSec)

Este documento adapta y formaliza los estandares de desarrollo del equipo para el proyecto `academiahacking_ucncqbo` (Backend FastAPI, contenedores Docker de retos y contratos/interfaces web asociadas).

---

## 1. Metodologia de Entrega Paso a Paso

No se permite iniciar una nueva tarea ni fase hasta dar por finalizada y verificada la tarea anterior.

1. **Definition of Ready (DoR)**: Toda tarea debe contar con alcance acotado, archivos objetivo identificados y criterio de aceptacion verificable.
2. **Flujo por rama**:
   - Prohibido trabajar directamente sobre `main`.
   - Convencion de ramas: `feat/<tema>`, `fix/<tema>`, `sec/<tema>`, `refactor/<tema>`, `docs/<tema>`.
   - Commits atomicos bajo Conventional Commits (`feat:`, `fix:`, `security:`, `refactor:`, `docs:`, `test:`, `chore:`) en idioma consistente y sin emojis.
3. **Definition of Done (DoD)**:
   - Implementacion completa sin codigo muerto ni `TODO` sin ticket asociado.
   - Sin emojis ni comentarios innecesarios en ningun archivo tocado.
   - Verificacion automatizada ejecutada (`pytest`, linter, chequeo de contenedores o validacion documental) despues del ultimo cambio.
   - Documentacion tecnica actualizada si hubo cambios en API, variables de entorno o arquitectura.

---

## 2. Clean Code, SOLID y Disciplina de Codigo

### Reglas de Estilo Innegociables

- **Cero emojis**: Prohibido usar emojis o simbolos graficos decorativos en codigo fuente, mensajes de respuesta API, logs, scripts, docstrings, commits o documentacion.
- **Cero comentarios innecesarios**: No escribir comentarios que repitan lo que hace el codigo ni separadores visuales decorativos (`# ----`). Comentar unicamente el *por que* de decisiones no obvias o invariantes de seguridad. Prohibido dejar bloques de codigo comentado en el repositorio.
- **Funciones pequenas y cohesivas**: Profundidad maxima de anidacion de 3 niveles; preferir retornos tempranos (*guard clauses*) y extraccion de helpers sin duplicar logica.

### Aplicacion Practica de SOLID en el Backend (FastAPI + SQLAlchemy)

| Principio | Regla Aplicada al Proyecto |
|---|---|
| **S - Single Responsibility** | Los routers (`api/v1/`) solo traducen HTTP y validan esquemas; los servicios orquestan casos de uso; los repositorios ejecutan consultas SQL; `security.py` solo opera primitivas criptograficas. |
| **O - Open/Closed** | La verificacion de flags (estatica HMAC, dinamica por instancia) y los modos de provision de retos (hosted URL vs CLI local) deben modelarse mediante estrategias extensibles sin cascadas de `if/elif`. |
| **L - Liskov Substitution** | Cualquier implementacion de repositorio (PostgreSQL, SQLite en test o memoria) debe respetar exactamente el contrato de tipos, excepciones y semantica definido en su interfaz `Protocol`. |
| **I - Interface Segregation** | Segregar esquemas Pydantic por contexto (`ChallengePublic`, `ChallengeAdmin`, `InstanceChallengeInfo`; `UserPublicProfile`, `UserPrivateProfile`, `UserAdminProfile`). Nunca reutilizar DTOs con PII o secretos en vistas publicas. |
| **D - Dependency Inversion** | Los servicios deben recibir repositorios y configuracion por inyeccion de dependencias (`Depends`), evitando metodos estaticos acoplados directamente a `AsyncSession` o globales mutables. |

---

## 3. Patrones de Diseno Obligatorios

### En Backend (Python / FastAPI)

1. **Repository Pattern + Unit of Work**: Encapsular todo acceso a `User`, `Challenge`, `Solve`, `Submission` y `ChallengeInstance` en repositorios dedicados para eliminar consultas ad-hoc en routers (`admin.py`, `ctf_academy.py`) y unificar reglas como el calculo de ranking.
2. **Dependency Injection**: Proveer sesion, repositorios y servicios a traves de `app/api/deps.py` para facilitar pruebas unitarias y desacoplar ciclo de vida.
3. **Strategy Pattern**: Desacoplar algoritmos intercambiables: verificacion de flags (`ConstantTimeHmacVerifier`) y generacion de URLs/metadatos de lanzamiento de retos.
4. **Adapter Pattern**: Mantener `/api/ctf-academy` estrictamente como un adaptador delgado que traduce el formato RPC hacia los servicios canonicos de `v1`, sin duplicar logica de negocio ni de ranking.
5. **Application Factory**: Construccion de la instancia `FastAPI` mediante una funcion `create_app(settings)` que facilite configuraciones aisladas para pruebas, desarrollo y produccion.

### En Frontend (`eclipsec.cl`) y Vistas Web de Retos (`docker/`)

1. **Component Composition & Generic UI Primitives**: Construir bloques reutilizables parametrizados por variantes en lugar de duplicar tarjetas, botones, tablas o formularios por pagina.
2. **BFF (Backend for Frontend) / Service Facade**: Toda llamada autenticada desde el navegador hacia la API del backend debe encapsularse detras de handlers de servidor en Next.js (Route Handlers / Server Actions) o cookies `HttpOnly`, ocultando credenciales y tokens de la red del navegador.
3. **Skeleton Loading Pattern**: Toda vista asincrona debe definir su componente Skeleton acoplado a la geometria del componente real.

---

## 4. DevSecOps y Principios de Seguridad

### 4.1 Cero Tokens Expuestos en Vistas de Red desde Navegadores

Queda estrictamente prohibido en el portal web:

- Almacenar JWTs o tokens de sesion en `localStorage`, `sessionStorage` o variables globales de JavaScript.
- Devolver tokens JWT en el cuerpo JSON de login/registro hacia codigo JavaScript del navegador.
- Enviar cabeceras `Authorization: Bearer <token>` desde codigo cliente en el navegador (visibles y copiables directamente desde las herramientas de red o vulnerables a robo via XSS).

**Arquitectura Obligatoria de Sesion para Navegadores:**

1. El frontend Next.js actua como **BFF (Backend for Frontend)** o el backend emite una cookie de sesion opaca/firmada con atributos `HttpOnly; Secure; SameSite=Lax; Path=/`.
2. En el flujo BFF: el navegador envia credenciales una sola vez al endpoint del propio origen Next.js; el servidor Next.js autentica contra FastAPI, almacena la sesion cifrada o en cookie `HttpOnly` firmada y reenvia las peticiones posteriores desde el servidor.
3. En la pestana Network del navegador del usuario nunca deben aparecer tokens Bearer ni secretos en payloads JSON o cabeceras manipulables por JavaScript.
4. Toda mutacion via cookie debe validar proteccion CSRF (`SameSite=Lax` + verificacion de cabecera `Origin`/`Referer` o token double-submit).
5. **Excepcion acotada para `eclipsecCLI`**: El CLI de terminal no es un navegador; debe usar un flujo separado de token de CLI con alcance restringido (solo lectura de retos e instancias/envio de flags), expiracion acotada y almacenamiento en el almacen de credenciales del sistema operativo.

### 4.2 Gestion de Secretos, `.env.example` y Flags CTF

- Ningun secreto (`JWT_SECRET`, `ADMIN_PASSWORD`, `FLAG_HMAC_SECRET`, credenciales de BD) ni ninguna flag real de competencia debe vivir en el historial de Git ni como valor por defecto usable en produccion.
- Los archivos plantilla como `.env.example` deben usar exclusivamente valores 100% ficticios (`example.test`, `example.local`, `example-org/example-ctf-challenges`, `ENVIRONMENT="development"`), sin parecerse a dominios, repositorios, usuarios ni credenciales reales.
- La aplicacion debe fallar de inmediato al arrancar (`fail-fast`) si `ENVIRONMENT == "production"` y faltan secretos obligatorios o tienen entropia insuficiente (< 32 caracteres).
- Las flags deben verificarse en tiempo constante (`hmac.compare_digest`) contra un resumen criptografico con clave (`HMAC-SHA256`), nunca almacenarse en texto plano en `challenges` ni en `submissions`.

### 4.3 Hardening de API, Contenedores y Portabilidad Multi-SO

- **RBAC explicito**: Prohibida la asignacion automatica del rol `admin` en el registro publico.
- **CORS estricto**: Prohibido usar wildcards amplios como `https://*.vercel.app` junto con `allow_credentials=True`. Listar origenes exactos y metodos/cabeceras minimos necesarios.
- **Rate Limiting**: Aplicar limites de tasa diferenciados para autenticacion, registro y envio de flags.
- **Privacidad y Minimizar PII**: Ningun endpoint publico puede exponer `email`, estado interno `is_active` ni roles de otros usuarios.
- **Frontera Pedagogica e Invariante Anti-Bypass en Contenedores CTF**:
  - Cada reto vulnerable intencional (SQLi, LFI, SSTI, CMDi) debe aislarse bajo usuario sin privilegios (`ctf` en standalone; `web002`..`web011` en monolitico) con permisos restrictivos (`0550`/`0440` o `0700`/`0440`) y limites de recursos (`mem_limit`, `cpus`, `pids_limit`).
  - Prohibido incluir terminales interactivas (`ttyd` / shells) dentro de los contenedores victima o variables `ENV FLAG=` globales que permitan leer flags sin completar la vulnerabilidad del reto.
  - La vulnerabilidad debe permitir leer exclusivamente la flag de *ese* reto especifico tras explotar el vector intencional (ej. path traversal real en LFI, sin atajos en el directorio de trabajo).
- **Portabilidad Multi-SO (Windows, Linux, macOS)**:
  - Toda ruta de archivo en backend y generadores debe construirse con `pathlib.Path(__file__).resolve()` y normalizarse con `.as_posix()` en URIs SQLite para no depender del directorio de trabajo (`CWD`) ni de separadores especificos del sistema operativo.
  - `.gitattributes` debe forzar saltos de linea `eol=lf` en scripts `.sh`, Dockerfiles, Python, YAML, TOML y JSON para evitar fallos al construir o arrancar contenedores Linux desde estaciones Windows.

---

## 5. Estandares de Frontend, Diseno Visual, SEO y UX

Estos estandares rigen tanto para el portal principal `eclipsec.cl` como para las plantillas web de los retos CTF alojados en `docker/`.

### 5.1 Colorimetria Centralizada en `global.css` y Regla 60-30-10

Todos los colores, tipografias, radios y espaciados deben vivir exclusivamente como Custom Properties en un archivo central `global.css`. Queda prohibido usar colores hexadecimales hardcodeados o atributos `style="..."` en componentes y plantillas HTML.

La paleta debe distribuirse estrictamente bajo la **Regla 60-30-10**:

- **60% Dominante**: Fondos principales, lienzo de pagina y grandes superficies de descanso visual (`--color-bg-primary`, `--color-bg-canvas`).
- **30% Apoyo**: Bloques contenedores, tarjetas de retos, barras laterales, bordes sutiles y textos secundarios (`--color-surface-card`, `--color-surface-elevated`, `--color-border-subtle`, `--color-text-secondary`).
- **10% Acento**: Llamadas a la accion primarias (botones de envio de flag, inicio de instancia), indicadores activos y estados criticos (`--color-accent-primary`, `--color-accent-hover`, `--color-status-success`, `--color-status-error`).

**Plantilla Base de Referencia (`global.css`)**:

```css
:root {
  --color-bg-primary: #0b0f17;
  --color-bg-canvas: #0f1522;

  --color-surface-card: #161e2e;
  --color-surface-elevated: #1e293b;
  --color-border-subtle: #2b384e;
  --color-text-primary: #f1f5f9;
  --color-text-secondary: #94a3b8;

  --color-accent-primary: #e11d48;
  --color-accent-hover: #be123c;
  --color-accent-contrast: #ffffff;
  --color-focus-ring: #fb7185;

  --color-status-success: #10b981;
  --color-status-warning: #f59e0b;
  --color-status-error: #ef4444;

  --font-sans: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
  --font-mono: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;

  --text-xs: 0.75rem;
  --text-sm: 0.875rem;
  --text-base: 1rem;
  --text-lg: 1.125rem;
  --text-xl: 1.5rem;
  --text-2xl: 2rem;

  --leading-tight: 1.2;
  --leading-normal: 1.55;
  --measure-prose: 65ch;

  --space-1: 0.25rem;
  --space-2: 0.5rem;
  --space-3: 0.75rem;
  --space-4: 1rem;
  --space-6: 1.5rem;
  --space-8: 2rem;
  --space-12: 3rem;

  --radius-sm: 0.375rem;
  --radius-md: 0.625rem;
  --radius-lg: 0.875rem;
}

*,
*::before,
*::after {
  box-sizing: border-box;
}

body {
  margin: 0;
  background-color: var(--color-bg-primary);
  color: var(--color-text-primary);
  font-family: var(--font-sans);
  font-size: var(--text-base);
  line-height: var(--leading-normal);
}

:focus-visible {
  outline: 2px solid var(--color-focus-ring);
  outline-offset: 2px;
}
```

### 5.2 Componentes Genericos Reutilizables

Antes de crear un componente nuevo, es obligatorio verificar si puede resolverse componiendo o parametrizando los primitivos genericos existentes:

| Componente Generico | Responsabilidad y Variantes |
|---|---|
| `Container` / `PageSection` | Ancho maximo consistente, padding responsivo y landmarks semanticos |
| `PageHeader` | Encabezado unico (`h1`), subtitulo acotado a `65ch` y acciones contextuales |
| `Button` | Variantes `primary` (10% acento), `secondary` (30% apoyo), `ghost`, `danger`; estados `loading` y `disabled` |
| `Card` | Contenedor de superficie apoyo (`30%`) con cabecera, cuerpo y pie opcionales |
| `Badge` | Etiquetas de dificultad (`EASY`, `MEDIUM`, `HARD`, `INSANE`), categoria y estado de resolucion |
| `FormField` + `Input` | Etiqueta `<label>` asociada, control accesible, texto de ayuda y mensaje de error |
| `DataTable` | Tabla semantica (`<table>`, `<thead>`, `<tbody>`, `scope="col"`) para leaderboard y administracion |
| `Modal` / `Dialog` | Ventana accesible con trap de foco y cierre con `Escape` para detalle de reto y envio de flag |
| `Alert` | Mensajes de retroalimentacion (`success`, `warning`, `error`, `info`) con `role="status"` o `role="alert"` |
| `Skeleton` | Placeholder animado reutilizable (`line`, `card`, `table-row`, `stat-tile`) |

### 5.3 HTML Estructurado y SEO

1. **Semantica obligatoria**:
   - Usar `<header>`, `<nav aria-label="...">`, `<main id="main-content">`, `<section>`, `<article>`, `<aside>` y `<footer>` en lugar de `<div>` genericos.
   - Exactamente un `<h1>` por vista y jerarquia estricta sin saltos (`h1` -> `h2` -> `h3`).
   - Botones de accion con `<button type="button|submit">` y navegacion con `<a href="...">`.
2. **Metadatos e Indexacion**:
   - `<html lang="es">` y `<title>` unico por ruta (`<Titulo Vista> | EclipSec CTF`).
   - `<meta name="description">` de 140 a 160 caracteres, `<link rel="canonical">`, Open Graph (`og:title`, `og:description`, `og:type`, `og:url`) y datos estructurados JSON-LD (`WebSite`, `EducationalOrganization`, `BreadcrumbList`).
   - `sitemap.xml` y `robots.txt` configurados para indexar paginas publicas del portal y excluir rutas privadas (`/admin`, `/api`, `/profile` privado).
   - **Regla especifica para contenedores de retos CTF (`docker/`)**: Incluir `<meta name="robots" content="noindex, nofollow">` y cabecera `X-Robots-Tag: noindex, nofollow` en las aplicaciones vulnerables para que los buscadores no indexen sandboxes de laboratorio como sitios productivos.

### 5.4 Skeletons para Experiencia de Usuario

- Toda carga de datos asincronos (catalogo de retos, tabla de ranking, perfil de usuario, detalle de reto) debe renderizar un `Skeleton` con dimensiones equivalentes al contenido final para evitar saltos de diseno (`CLS < 0.1`).
- Los contenedores en carga deben exponer `aria-busy="true"` y respetar `@media (prefers-reduced-motion: reduce)` deteniendo las animaciones shimmer.

### 5.5 Reglas de Tipografia, Longitud de Linea, Densidad y Espaciado

| Propiedad | Estandar Obligatorio |
|---|---|
| Tamano base de texto | `16px` (`1rem`) en cuerpo; nunca menor a `12px` (`0.75rem`) en etiquetas o metadatos |
| Ancho de linea (`measure`) | Entre `45ch` y `75ch` (`max-width: 65ch` en descripciones de retos, pistas y texto narrativo) |
| Interlineado (`line-height`) | `1.5` a `1.65` en parrafos y tablas; `1.15` a `1.25` en encabezados |
| Densidad de texto | Parrafos de maximo 3 a 4 lineas (40-60 palabras); tarjetas de reto con titulo breve (<= 60 caracteres) y resumen truncado a 2 lineas |
| Escala de espaciado | Multiplos estrictos de `4px` / `8px` (`--space-1` a `--space-12`), con `gap` minimo de `16px` entre tarjetas y `24px–32px` entre secciones |
| Contraste (WCAG AA) | Minimo `4.5:1` en texto normal y `3:1` en texto grande, iconos y bordes de campos interactivos |

---

## 6. Checklist de Revision de Pull Requests

Antes de aprobar o fusionar cualquier cambio, verificar todos los puntos aplicables:

- [ ] La tarea pertenece al paso activo de la hoja de ruta y cierra todos sus criterios de aceptacion.
- [ ] Cero emojis y cero comentarios redundantes o codigo comentado en la diferencia (`git diff`).
- [ ] Cero secretos, credenciales reales o flags de competencia en archivos versionados.
- [ ] Ninguna vista o guia web expone tokens JWT en `localStorage` ni en cabeceras `Authorization` enviadas desde el navegador.
- [ ] Cambios backend respetan separacion de capas, validacion de entrada y tienen pruebas unitarias/integracion en verde.
- [ ] Cambios HTML/CSS usan variables de `global.css` bajo proporcion 60-30-10, HTML semantico, skeletons en carga y respetan longitudes de linea y espaciado.
