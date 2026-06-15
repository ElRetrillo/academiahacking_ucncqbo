# Guía de Despliegue de Retos CTF en Railway (EclipSec)

Este documento detalla la diferencia arquitectónica entre un despliegue Docker tradicional y la plataforma Railway, con el objetivo de planificar correctamente la conexión de los retos desde `eclipsec.cl`.

## 1. El Problema de los Puertos: Local vs Railway

El diseño inicial de los retos (como el `challenge-web-001`) y el archivo `docker-compose.yml` están pensados para un entorno **Docker tradicional** (ya sea en tu entorno local o en un servidor VPS como DigitalOcean, AWS o Hetzner).

### Entorno Docker Tradicional (VPS o Local)
En un servidor normal, el `docker-compose.yml` mapea directamente múltiples puertos hacia el exterior. Por ejemplo:
- Reto 1: `http://TU_IP:8001`
- Reto 2: `http://TU_IP:8002`
- Reto 3: `http://TU_IP:8003`

### Entorno Railway
Railway (y plataformas similares como Render o Heroku) funciona con una arquitectura Serverless/PaaS que es diferente:
- A cada "Servicio" se le asigna un **único dominio** (ej. `mis-retos.up.railway.app`).
- Ese dominio **únicamente expone los puertos web estándar (80 y 443)**.
- **Railway ignora las directivas de puertos como `8001:80`** de tu `docker-compose.yml` de cara al exterior. El tráfico siempre entrará por el puerto 443 (HTTPS) y Railway lo enrutará internamente al puerto único que tu aplicación exponga (usualmente el 80, 8080 o `$PORT`).

## 2. Impacto en la Plataforma EclipSec

Esto significa que si intentas desplegar todos los retos juntos en un solo servicio de Railway, **no podrás** hacer que los usuarios entren a `mis-retos.up.railway.app:8001` o `:8002`. Solo uno de los retos será accesible públicamente, o la aplicación simplemente fallará en rutear el tráfico.

## 3. Soluciones para Implementar la Conexión

Para lograr que los 11 retos estén disponibles para los usuarios de `eclipsec.cl`, existen tres caminos a seguir:

### Solución A: Múltiples Servicios en Railway (Fácil pero consume más recursos)
La forma más "limpia" dentro de Railway es crear **11 servicios distintos** dentro del mismo Proyecto.
- Conectas el mismo repositorio de GitHub a cada servicio.
- Configuras cada servicio para que apunte a un `Dockerfile` diferente (ej: `docker/challenge-web-001/Dockerfile`).
- Railway le dará a cada reto un subdominio único.
- En tu frontend `challenges.ts`, configurarías las URLs así:
  - `https://reto1-eclipsec.up.railway.app`
  - `https://reto2-eclipsec.up.railway.app`

### Solución B: "Super-Contenedor" Monolítico con Nginx (Ahorra dinero en Railway)
Si quieres usar un solo servicio de Railway, debes combinar los 11 retos.
- Se debe crear un único `Dockerfile` gigante.
- Configurar un servidor `Nginx` principal que actúe como "Reverse Proxy".
- El Nginx recibirá todo el tráfico por el puerto 80 y lo enviará a los distintos retos según la ruta de la URL:
  - `https://retos-eclipsec.up.railway.app/web-001/`
  - `https://retos-eclipsec.up.railway.app/web-002/`
- *Nota:* Esta opción es la más compleja técnicamente porque requiere adaptar los retos para que funcionen bien bajo sub-rutas.

### Solución C: Migrar a un VPS Tradicional (Recomendado para CTFs)
Dado que los CTFs requieren configuraciones de red específicas y puertos abiertos (especialmente para retos como el `ttyd` que usa websockets, o para retos de `netcat`), la norma en la industria es alojar los contenedores en un **VPS económico** (como Hetzner por ~$4 USD al mes, o DigitalOcean).
- En un VPS, tu `docker-compose.yml` funcionará exactamente igual que en tu máquina local.
- Solo tendrías que apuntar un subdominio (ej: `ctf.eclipsec.cl`) a la IP de tu VPS.
- Tu frontend se conectaría limpiamente a `http://ctf.eclipsec.cl:8001`, `http://ctf.eclipsec.cl:8002`, etc.

---

**Siguiente paso recomendado:** 
Evaluar el presupuesto y la arquitectura deseada. Si se decide continuar con Railway, se debe elegir entre la **Solución A** (Modificar el frontend para usar múltiples URLs de Railway) o la **Solución B** (Modificar el backend para enrutar todo en un contenedor monolítico).
