# Academia de Hacking Competitivo UCN Coquimbo (EclipSec CTF)

Plataforma backend e infraestructura de retos CTF de la Academia de Hacking Competitivo de la Universidad Catolica del Norte (Sede Coquimbo), integrada dentro de la carpeta conjunta `CTF-Academia_cyber` junto con el portal web **EclipSec** (`EclipSec-WebPage`) y el cliente de consola **eclipsec-cli**.

---

## Repositorios Relacionados (`CTF-Academia_cyber`)

- `academiahacking_ucncqbo` (este repositorio): API FastAPI, migraciones Alembic y 11 retos web Docker (`docker/`).
- `../EclipSec-WebPage`: Portal Web React + TypeScript + Vite con sesion por cookies `HttpOnly` + `X-CSRF-Token`, sistema `global.css` 60-30-10, componentes genericos, Skeletons y SEO semantico.
- `../eclipsec-cli`: Cliente CLI Python para autenticacion, catalogo, ranking y ejecucion local de retos con Docker.

---

## Documentacion del Proyecto

Toda la documentacion tecnica, arquitectura, estandares de ingenieria y hoja de ruta se encuentra organizada en `docs/`:

- [Auditoria Tecnica y Hoja de Ruta](docs/PROJECT_AUDIT.md): Inventario real del repositorio, hallazgos de seguridad DevSecOps, deuda tecnica y plan de ejecucion paso a paso.
- [Arquitectura del Sistema](docs/ARCHITECTURE.md): Diagramas de ecosistema, capas del backend, modelo entidad-relacion, flujos de secuencia y ADRs.
- [Estandares de Ingenieria y Diseno](docs/STANDARDS.md): Reglas adaptadas de Clean Code, SOLID, patrones de diseno, DevSecOps (cero tokens expuestos en navegador), colorimetria 60-30-10 en `global.css`, HTML semantico/SEO, skeletons y tipografia.
- [Referencia de la API](docs/API_REFERENCE.md): Contratos de endpoints REST (`/api/v1/*`), adaptador heredado (`/api/ctf-academy`) y patron de integracion segura BFF para Next.js.
- [Catalogo de Retos e Infraestructura](docs/CHALLENGES_AND_INFRA.md): Listado de los 12 retos vigentes, despliegue con Docker Compose, nodo monolitico, flujo CLI y guia para nuevos retos.

---

## Estructura del Repositorio

```text
academiahacking_ucncqbo/
  backend/                  API FastAPI + SQLAlchemy Async + pruebas pytest
  docker/                   Contenedores de retos (challenge-web-001..011, monolithic, compose)
  docs/                     Documentacion tecnica, auditoria y estandares
  railway.toml              Configuracion de compilacion Docker para Railway
  RAILWAY_DEPLOYMENT_GUIDE.md  Notas iniciales de arquitectura de puertos en Railway
```

---

## Inicio Rapido (Backend Local)

Consulta la guia detallada de configuracion local, variables de entorno y ejecucion de pruebas en [backend/README.md](backend/README.md).

Resumen de comandos en PowerShell (Windows):

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python seed.py
uvicorn app.main:app --reload --port 8000
```

La especificacion OpenAPI interactiva queda disponible en `http://localhost:8000/docs`.

---

## Integracion Segura con Frontend Web

Las aplicaciones web que consuman esta API deben evitar almacenar tokens JWT en `localStorage` o exponer cabeceras `Authorization: Bearer` desde JavaScript del navegador. El patron oficial de integracion utiliza un **BFF (Backend for Frontend)** en Next.js con sesion gestionada mediante cookies `HttpOnly; Secure; SameSite=Lax`, detallado en [docs/STANDARDS.md](docs/STANDARDS.md) y [docs/API_REFERENCE.md](docs/API_REFERENCE.md).
