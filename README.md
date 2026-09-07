# Community & Watch Party Service

Servicio de comunidades para usuarios, clubes, membresías y salas de watch party. Usa MySQL y expone una API REST con FastAPI.

El alcance de este servicio termina en la gestión de salas y participantes. No implementa chat, WebSockets ni sincronización de reproducción; esas capacidades pertenecen a un servicio realtime separado con MongoDB.

## Requisitos

- Python 3.12 (para ejecución local)
- Docker Engine con Docker Compose v2 (para contenedores)

## Configuración

Copie el ejemplo y reemplace todos los secretos antes de iniciar:

```bash
cp .env.example .env
```

Variables principales:

| Variable | Propósito |
| --- | --- |
| `DATABASE_URL` | URL SQLAlchemy completa. Si se deja vacía se genera desde `MYSQL_*`. |
| `MYSQL_HOST` | Host de MySQL; en Compose debe ser `db`, nunca `localhost`. |
| `MYSQL_PORT`, `MYSQL_DATABASE`, `MYSQL_USER`, `MYSQL_PASSWORD` | Conexión de la API y creación de la base MySQL. |
| `MYSQL_ROOT_PASSWORD` | Contraseña administrativa requerida por el contenedor MySQL. |
| `JWT_SECRET` | Secreto obligatorio para firmar JWT; use un valor aleatorio de al menos 32 caracteres. |
| `API_PORT` | Puerto publicado de la API (por defecto `8000`). |

`DATABASE_URL` tiene prioridad sobre las variables `MYSQL_*`. No incluya `.env` en la imagen ni en el repositorio.

## Ejecución local

Instale dependencias y configure `.env` para apuntar a una instancia MySQL accesible:

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
alembic upgrade head
uvicorn app.main:app --reload
```

En macOS/Linux, active con `source .venv/bin/activate`. Swagger queda disponible en `http://localhost:8000/docs`.

## Docker Compose

```bash
docker compose up --build -d
docker compose ps
docker compose logs -f api
```

La API se publica en `http://localhost:${API_PORT:-8000}` y MySQL no se publica al host: ambos contenedores se comunican mediante la red privada `community_private`. Los datos residen en el volumen nombrado `community_mysql_data` y sobreviven a recreaciones de contenedores.

Verifique disponibilidad:

```bash
curl http://localhost:8000/api/v1/health
```

Para detener sin eliminar datos:

```bash
docker compose down
```

## Migraciones

La API aplica `alembic upgrade head` antes de iniciar. Para ejecutarlo manualmente:

```bash
alembic upgrade head
```

Las migraciones no cargan datos de desarrollo. Una instalación limpia crea `users`, `clubs`, `memberships`, `watch_rooms` y `watch_participants`. La migración más reciente elimina la antigua tabla de sincronización de playback.

## Endpoints públicos

La documentación interactiva está en `/docs`. Las rutas REST son:

| Área | Endpoint |
| --- | --- |
| Estado | `GET /api/v1/health` |
| Autenticación | `POST /api/v1/auth/register`, `POST /api/v1/auth/login` |
| Usuarios | `GET /api/v1/users`, `GET /api/v1/users/me`, `GET /api/v1/users/{id}`, `PUT/DELETE /api/v1/users/{id}` |
| Clubes | `POST/GET /api/v1/clubs`, `GET/PUT/DELETE /api/v1/clubs/{id}` |
| Membresías | `POST/GET /api/v1/clubs/{id}/members`, `GET /api/v1/users/{id}/clubs`, `PATCH /api/v1/clubs/{id}/members/{user_id}/role`, `DELETE /api/v1/clubs/{id}/members/{user_id}` |
| Watch rooms | `POST /api/v1/watch-rooms`, `GET /api/v1/watch-rooms/{code}`, `POST /api/v1/watch-rooms/{code}/join`, `DELETE /api/v1/watch-rooms/{code}/participants/{user_id}` |

Los roles de membresía son `OWNER`, `ADMIN` y `MEMBER`. Al crear un club, su creador se registra automáticamente como `OWNER`.

### Ejemplos de requests

Registrar un usuario:

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"ana","email":"ana@example.com","password":"secret123","display_name":"Ana"}'
```

Autenticarse (el endpoint usa formulario OAuth2):

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=ana&password=secret123"
```

Crear un club:

```bash
curl -X POST http://localhost:8000/api/v1/clubs \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"name":"Fans del cine","description":"Comunidad para hablar de películas","visibility":"PUBLIC"}'
```

Crear una sala (no sincroniza reproducción):

```bash
curl -X POST http://localhost:8000/api/v1/watch-rooms \
  -H "Content-Type: application/json" \
  -d '{"movieId":"550e8400-e29b-41d4-a716-446655440000","hostUserId":1,"clubId":1}'
```

### Flujo para crear una comunidad

1. Registre el usuario y obtenga un JWT con `/auth/login`.
2. Cree el club autenticado con `POST /clubs`; el usuario queda como `OWNER`.
3. Otros usuarios se unen con `POST /clubs/{id}/members` si el club es `PUBLIC`.
4. El `OWNER` puede asignar `ADMIN` o `MEMBER`; los administradores pueden editar el club y gestionar miembros.
5. Cree una watch room asociada opcionalmente al club. Para reproducción sincronizada o chat, integre el servicio realtime separado.

## Despliegue en una VM

1. Instale Docker Engine y el plugin Docker Compose en la VM.
2. Copie los archivos `docker-compose.yml` y `.env` seguro, o use la imagen publicada junto con estos archivos.
3. Genere secretos robustos y asegure que `MYSQL_HOST=db` y `DATABASE_URL` esté vacío (o use una URL remota válida).
4. Ejecute `docker compose pull && docker compose up -d`.
5. Publique únicamente el puerto de la API detrás de un proxy TLS (Nginx, Caddy o balanceador). No exponga MySQL.
6. Verifique `docker compose ps`, `/api/v1/health` y configure copias de seguridad del volumen MySQL.

## Publicar en Docker Hub

```bash
docker login
docker build -t antony17xd/community-service:v1 .
docker push antony17xd/community-service:v1
```

En la VM, defina la misma etiqueta en `docker-compose.yml` y ejecute `docker compose pull && docker compose up -d`.

## Validación

```bash
pytest -q
docker compose config
docker build -t antony17xd/community-service:v1 .
```
