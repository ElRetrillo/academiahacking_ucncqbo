# Guia de Despliegue de Retos CTF en Railway (EclipSec)

Este documento detalla la diferencia arquitectonica entre un despliegue Docker tradicional y la plataforma Railway, con el objetivo de planificar correctamente la conexion de los retos desde `eclipsec.cl`.

## 1. El Problema de los Puertos: Local vs Railway

El diseno inicial de los retos (como el `challenge-web-001`) y el archivo `docker-compose.yml` estan pensados para un entorno **Docker tradicional** (ya sea en tu entorno local o en un servidor VPS como DigitalOcean, AWS o Hetzner).

### Entorno Docker Tradicional (VPS o Local)
En un servidor normal, el `docker-compose.yml` mapea directamente multiples puertos hacia el exterior. Por ejemplo:
- Reto 1: `http://TU_IP:8001`
- Reto 2: `http://TU_IP:8002`
- Reto 3: `http://TU_IP:8003`

### Entorno Railway
Railway (y plataformas similares como Render o Heroku) funciona con una arquitectura PaaS diferente:
- A cada "Servicio" se le asigna un **unico dominio** (ej. `mis-retos.up.railway.app`).
- Ese dominio **unicamente expone los puertos web estandar (80 y 443)**.
- **Railway ignora las directivas de puertos como `8001:80`** de tu `docker-compose.yml` de cara al exterior. El trafico siempre entrara por el puerto 443 (HTTPS) y Railway lo enrutara internamente al puerto unico que tu aplicacion exponga (usualmente el 80, 8080 o `$PORT`).

## 2. Impacto en la Plataforma EclipSec

Esto significa que si intentas desplegar todos los retos juntos en un solo servicio de Railway, **no podras** hacer que los usuarios entren a `mis-retos.up.railway.app:8001` o `:8002`. Solo uno de los retos sera accesible publicamente, o la aplicacion simplemente fallara en rutear el trafico.

## 3. Soluciones para Implementar la Conexion

Para lograr que los 11 retos esten disponibles para los usuarios de `eclipsec.cl`, existen tres caminos a seguir:

### Solucion A: Multiples Servicios en Railway (Mayor aislamiento por servicio)
La forma mas limpia dentro de Railway para aislar cada entorno es crear **11 servicios distintos** dentro del mismo Proyecto:
- Conectas el mismo repositorio de GitHub a cada servicio.
- Configuras cada servicio para que apunte a un `Dockerfile` diferente (ej: `docker/challenge-web-001/Dockerfile`).
- Railway le dara a cada reto un subdominio unico y aislamiento de contenedor independiente.

### Solucion B: Contenedor Monolitico con Nginx (Menor costo en Railway)
Si se utiliza un unico servicio para los 11 retos web, se usa `docker/monolithic/Dockerfile`:
- Un servidor `Nginx` principal actua como Reverse Proxy.
- Enruta por sub-ruta hacia los procesos aislados por UID (`web002`..`web011`):
  - `https://retos.example.test/web-001/` a `/web-011/`

### Solucion C: Migrar a un VPS Tradicional (Recomendado para CTFs con multiples puertos)
Dado que los CTFs pueden requerir configuraciones de red especificas y puertos independientes (como TCP/netcat o servicios aislados por reto con limites de recursos), lo estandar es alojar los contenedores en un **VPS** con Docker Compose:
- En un VPS, `docker/docker-compose.yml` funciona exponiendo directamente `8001`..`8011` o detras de un proxy TLS por subdominio/puerto.
- El backend consume la URL base mediante `CHALLENGES_BASE_URL` o URLs absolutas por reto.
