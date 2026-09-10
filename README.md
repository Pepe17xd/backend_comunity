# Cinema Club Online — Community Service

Microservicio FastAPI para perfiles sociales, clubes, membresías y salas de watch party. La autenticación está centralizada en **identity-service**: Community no registra usuarios, no recibe contraseñas y no emite JWT.

## Contrato de identidad

El frontend inicia sesión únicamente en `identity-service` (puerto 9000) y envía el mismo encabezado a Community y Catalog:

```http

Authorization: Bearer <identity JWT>

```

Community valida la firma, algoritmo, `iss` y expiración del JWT. El token debe incluir `sub` como UUID, `iss`, `exp` y, recomendado para el perfil local, `username` y `email`. `sub` se guarda como `users.identity_user_id`; nunca se almacenan contraseñas. El primer acceso crea el perfil local. Si existe un perfil previo sin vínculo y su email coincide con el email verificado del JWT, se enlaza preservando sus clubes, roles, salas y participantes.

## Variables de entorno

| Variable | Uso |

| --- | --- |

| `DATABASE_URL` | URL SQLAlchemy; si falta se compone con `MYSQL_*`. |

| `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_DATABASE`, `MYSQL_USER`, `MYSQL_PASSWORD` | MySQL de Community. |

| `MYSQL_ROOT_PASSWORD` | Contraseña root usada solo por el contenedor MySQL. |

| `JWT_SECRET` | Mismo secreto de firma configurado en identity-service. |

| `JWT_ALGORITHM` | Mismo algoritmo de identity-service, por defecto `HS256`. |

| `JWT_ISSUER` | Emisor exacto esperado, por defecto `identity-service`. |

| `API_PORT` | Puerto publicado, por defecto `8000`. |

=======

Microservicio REST de comunidad con **FastAPI y Python 3.12**: usuarios, clubes, membresías y salas de watch party. Usa **MySQL 8.4**, **SQLAlchemy 2** con **Alembic**, contraseñas con **Argon2id** y tokens **JWT**.

## Rol en la arquitectura

Es el microservicio de **comunidad (Python + MySQL)** de la plataforma *Cinema Club Online*. Gestiona la identidad social de los usuarios, la creación de clubes de cine, el sistema de roles (membresías) y las salas de watch party. Responde preguntas como **"¿quién pertenece a cada club?"** o **"¿qué sala compartimos?"**.

En el árbol de llamadas, Community es una **hoja funcional**: sus endpoints se consumen directamente desde el frontend y no consume a otros microservicios; comparte el origen de identidad del resto de la plataforma mediante los JWT que emiten el Identity Service y él mismo. El alcance de este servicio termina en la gestión de salas y participantes: **no implementa chat, WebSockets ni sincronización de reproducción**; esas capacidades pertenecen a un servicio realtime separado con MongoDB.

Su base de datos relacional (MySQL) convive con las del Catalog Service (PostgreSQL) y el Identity Service (PostgreSQL); el Interaction Service usa MongoDB y el Experience Service no maneja base de datos propia.

## Stack

- Python 3.12

- FastAPI (con Pydantic v2 y `pydantic-settings`)

- SQLAlchemy 2 y MySQL 8.4

- Alembic (migraciones)

- JWT (`PyJWT`, HS256) y `pwdlib` (Argon2id)

- Docker / Docker Compose y Pytest

## Arquitectura de despliegue

Docker Compose ejecuta dos contenedores separados en la red privada `community_private` (**internal: true**, por lo que MySQL no es accesible desde el host):

- `api`: API publicada en el puerto `API_PORT` (8000 por defecto). Ejecuta `alembic upgrade head` antes de arrancar uvicorn.

- `db`: MySQL 8.4 con el volumen persistente `community_mysql_data` y healthcheck (`mysqladmin ping`).

Ambos contenedores tienen healthcheck: MySQL valida la conexión y la API consulta `GET /api/v1/health`.

## Variables de entorno

Copia el ejemplo antes de arrancar:

```powershell

Copy-Item .env.example .env

```

```bash

cp .env.example .env

```

| Variable | Requerida | Uso |

| --- | --- | --- |

| `DATABASE_URL` | No (prioridad sobre `MYSQL_*`) | URL SQLAlchemy completa. Si se deja vacía se genera desde `MYSQL_*`. |

| `MYSQL_HOST` | Sí (desde Compose) | Host de MySQL; en Compose debe ser `db`, nunca `localhost`. |

| `MYSQL_PORT` | No | Puerto de MySQL; por defecto `3306`. |

| `MYSQL_DATABASE` | No | Nombre de la base; por defecto `community_db`. |

| `MYSQL_USER` | No | Usuario de la API; por defecto `community`. |

| `MYSQL_PASSWORD` | Sí | Contraseña de MySQL. No subir al repositorio. |

| `MYSQL_ROOT_PASSWORD` | Sí | Contraseña administrativa requerida por el contenedor MySQL. |

| `JWT_SECRET` | Sí | Secreto obligatorio para firmar JWT; use un valor aleatorio de al menos 32 caracteres. |

| `JWT_ALGORITHM` | No | Algoritmo JWT; por defecto `HS256`. |

| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | Expiración del token; por defecto `60`. |

| `API_PORT` | No | Puerto publicado de la API; por defecto `8000`. |

>>>>>>> b3060d44607c468f3f643124be49e68466967a08

Copie `.env.example` a `.env`, reemplace secretos y asegure que los tres valores `JWT_*` coincidan con Identity. No incluya `.env` en la imagen.

## Cambios de payload del frontend

| Archivo/end-point | Antes | Después |

| --- | --- | --- |

| Cliente que llama `POST /api/v1/watch-rooms` | `{"movieId":"...", "hostUserId": 1, "clubId": 1}` | `{"movieId":"...", "clubId": 1}` + Bearer token |

| Cliente que llama `POST /api/v1/watch-rooms/{code}/join` | `{"userId": 2, "nickname":"Ana"}` | `{"nickname":"Ana"}` + Bearer token |

| Cliente que llama `DELETE /api/v1/watch-rooms/{code}/participants/{user_id}` | Sin requisito de identidad | Bearer token. Solo el propio participante, host, o `OWNER`/`ADMIN` del club asociado puede eliminar. |

| Cliente de login/registro Community | `POST /api/v1/auth/register` y `/login` | Eliminar estas llamadas. Use únicamente `identity-service /api/auth/login`. |

`POST /api/v1/clubs` ya utiliza el usuario derivado del Bearer token. No acepta un propietario en el body.

## Seguridad y permisos

- Tokens sin firma válida, expirados, sin `sub` UUID o sin `iss` esperado responden `401`.

- `hostUserId` y el identificador de unión ya no provienen del cliente.

- Las salas vinculadas a un club requieren membresía para crear o unirse.

- Se preservan los roles `OWNER`, `ADMIN`, `MEMBER`; permisos de clubes continúan aplicándose.

## Local

```bash

python -m venv .venv

.venv\Scripts\Activate.ps1       # en macOS/Linux: source .venv/bin/activate

pip install -r requirements-dev.txt

Copy-Item .env.example .env

# Edite .env con los JWT_* de identity-service y MySQL accesible

alembic upgrade head

pytest -q

uvicorn app.main:app --reload

```

Para una prueba manual, obtenga el JWT real desde `identity-service`, luego:

```bash

curl -X POST http://localhost:8000/api/v1/clubs -H "Authorization: Bearer <IDENTITY_JWT>" -H "Content-Type: application/json" -d "{\"name\":\"Fans del cine\",\"visibility\":\"PUBLIC\"}"

curl -X POST http://localhost:8000/api/v1/watch-rooms -H "Authorization: Bearer <IDENTITY_JWT>" -H "Content-Type: application/json" -d "{\"movieId\":\"550e8400-e29b-41d4-a716-446655440000\"}"

```

## Docker y producción

El `Dockerfile` aplica migraciones antes de levantar Uvicorn y ejecuta como usuario no root.

```bash

docker compose up --build -d

docker build -t antony17xd/community-service:v2 .

docker push antony17xd/community-service:v2

```

En producción, publique la imagen, actualice el `.env` seguro con el secreto, algoritmo y emisor de Identity, y ejecute:

=======

Swagger queda disponible en `http://localhost:8000/docs`. Si usa Docker Compose, la API arranca igual y queda en `http://localhost:8000`:

```bash

docker compose up --build -d

docker compose ps

docker compose logs -f api

curl http://localhost:8000/api/v1/health

```

Los datos residen en el volumen nombrado `community_mysql_data` y sobreviven a recreaciones de contenedores. Para detener sin eliminar datos: `docker compose down`.

### Validación

```bash

pytest -q

docker compose config

```

## Imagen Docker

El Dockerfile arranca desde `python:3.12.11-slim-bookworm` como usuario no privilegiado `app`, copia `app/`, `migrations/` y `alembic.ini`, y ejecuta la API con `alembic upgrade head` antes de uvicorn. Para construir y publicar la imagen:

```bash

docker build -t antony17xd/community-service:v1 .

docker login

docker push antony17xd/community-service:v1

```

`docker-compose.yml` conserva esa misma etiqueta en `image:` y también declara `build:` para desarrollo o CI. En una VM que deba usar únicamente la imagen publicada:

```bash

docker compose pull && docker compose up -d

```

## Migraciones e inicialización

Alembic versiona el esquema (`alembic.ini` + `migrations/`). La API aplica `alembic upgrade head` automáticamente al iniciar en el contenedor. El historial de migraciones:

- `001_initial.py` — crea `users`, `clubs` y `memberships`.

- `002_create_watch_rooms.py` — crea `watch_rooms`, `watch_participants` (y originalmente `playback_states`).

- `003_remove_playback_sync.py` — **elimina** `playback_states` (la sincronización de reproducción no pertenece a este servicio).

Las migraciones no cargan datos de desarrollo. Una instalación limpia termina con **5 tablas**: `users`, `clubs`, `memberships`, `watch_rooms` y `watch_participants`.

## Modelo de datos (MySQL)

| Tabla | Descripción y columnas principales |

| --- | --- |

| `users` | `id` (PK autoincrement), `username` (único), `email` (único), `display_name`, `bio`, `avatar_url`, `hashed_password`, `is_active`, `created_at`, `updated_at`. |

| `clubs` | `id` (PK), `name` (único), `description`, `owner_id` (FK → `users.id`), `visibility`, `is_active`, `created_at`, `updated_at`. |

| `memberships` | Puente N:M entre `users` y `clubs`: `user_id` (FK), `club_id` (FK), `role`, `joined_at`; **UNIQUE (`user_id`, `club_id`)**. |

| `watch_rooms` | `id` (UUID string PK), `code` (único), `club_id` (FK nullable), `host_user_id` (FK → `users.id`), `movie_id` (UUID string, referencia al catálogo), `status`, `created_at`, `updated_at`. |

| `watch_participants` | `watch_room_id` (FK), `user_id` (FK), `nickname`, `role`, `joined_at`; **UNIQUE (`watch_room_id`, `user_id`)**. |

Relaciones: `users` **1:N** `clubs` (owner) y **N:M** vía `memberships`; `clubs` **1:N** `watch_rooms`; `watch_rooms` **1:N** `watch_participants`; `users` **1:N** `watch_participants`. El `movie_id` de las salas referencia el UUID público que expone el Catalog Service, sin FK a nivel de base.

Enumerados que usa la API:

| Campo | Valores |

| --- | --- |

| `clubs.visibility` (`ClubVisibility`) | `PUBLIC`, `PRIVATE` |

| `memberships.role` (`MembershipRole`) | `OWNER`, `ADMIN`, `MEMBER` |

| `watch_rooms.status` (`WatchRoomStatus`) | `WAITING`, `PLAYING`, `PAUSED`, `FINISHED` |

| `watch_participants.role` (`WatchParticipantRole`) | `HOST`, `VIEWER` |

## API y uso de endpoints

Base URL local: `http://localhost:8000`. Prefijo común: `/api/v1`.

| Herramienta | URL |

| --- | --- |

| Swagger UI | `http://localhost:8000/docs` |

| OpenAPI (JSON) | `http://localhost:8000/openapi.json` |

| Health check | `GET http://localhost:8000/api/v1/health` |

Endpoint | Método | Descripción

--- | --- | ---

`/api/v1/health` | GET | Estado del servicio.

`/api/v1/auth/register` | POST | Registra un usuario.

`/api/v1/auth/login` | POST | Inicia sesión (formulario OAuth2) y devuelve un JWT.

`/api/v1/users/me` | GET | Perfil del usuario autenticado.

`/api/v1/users` | GET | Lista usuarios (paginado).

`/api/v1/users/{user_id}` | GET | Perfil de un usuario.

`/api/v1/users/{user_id}` | PUT | Actualiza tu propio perfil.

`/api/v1/users/{user_id}` | DELETE | Desactiva tu propio usuario.

`/api/v1/clubs` | POST | Crea un club (el creador queda como `OWNER`).

`/api/v1/clubs` | GET | Lista clubes (paginado).

`/api/v1/clubs/{club_id}` | GET | Detalle de un club.

`/api/v1/clubs/{club_id}` | PUT | Edita un club (requiere `OWNER`/`ADMIN`).

`/api/v1/clubs/{club_id}` | DELETE | Desactiva un club (solo `OWNER`).

`/api/v1/clubs/{club_id}/members` | POST | Únete a un club público.

`/api/v1/clubs/{club_id}/members` | GET | Lista los miembros del club.

`/api/v1/users/{user_id}/clubs` | GET | Lista los clubes de un usuario.

`/api/v1/clubs/{club_id}/members/{user_id}/role` | PATCH | Cambia el rol de un miembro (solo `OWNER`).

`/api/v1/clubs/{club_id}/members/{user_id}` | DELETE | Salir del club o expulsar a un miembro.

`/api/v1/watch-rooms` | POST | Crea una sala de watch party.

`/api/v1/watch-rooms/{code}` | GET | Detalle de una sala por código.

`/api/v1/watch-rooms/{code}/join` | POST | Une un usuario a la sala.

`/api/v1/watch-rooms/{code}/participants/{user_id}` | DELETE | Retira a un participante.

**Formato de error común** (FastAPI): `{"detail": "<mensaje>"}`, con el código HTTP correspondiente. Las respuestas `401` incluyen además la cabecera `WWW-Authenticate: Bearer`.

```json

{

  "detail": "Credenciales inválidas"

}

```

## Autenticación y tokens

Los tokens se firman con **HS256** y contienen `sub` (id del usuario) y `exp` por defecto a **60 minutos** (`ACCESS_TOKEN_EXPIRE_MINUTES`). Para autenticarte, incluye:

```text

Authorization: Bearer <access_token>

```

Los endpoints de usuarios y clubes exigen un token válido (firmado por el Community Service o por cualquier servicio que comparta `JWT_SECRET`); los de watch rooms son públicos y transportan `user_id`/`host_user_id` en el body.

### 1. `GET /api/v1/health` — estado del servicio

>>>>>>> b3060d44607c468f3f643124be49e68466967a08

```bash

docker compose pull

docker compose up -d

```

No exponga MySQL; publique Community detrás de TLS/proxy y conserve copias de seguridad del volumen.

=======

`200 OK`:

```json

{

  "status": "ok",

  "service": "community-service"

}

```

### 2. `POST /api/v1/auth/register` — registrar usuario

```bash

curl -X POST http://localhost:8000/api/v1/auth/register \

  -H "Content-Type: application/json" \

  -d '{"username":"ana","email":"ana@example.com","password":"secret123","display_name":"Ana"}'

```

Reglas: `username` entre 3 y 50; `email` con formato válido; `password` entre 8 y 128.

`201 Created` — `UserRead`:

```json

{

  "id": 1,

  "username": "ana",

  "email": "ana@example.com",

  "display_name": "Ana",

  "bio": null,

  "avatar_url": null,

  "is_active": true,

  "created_at": "2026-09-06T12:00:00",

  "updated_at": "2026-09-06T12:00:00"

}

```

| Código | Situación |

| --- | --- |

| `409` | El email o el username ya están registrados. |

| `422` | Validación de campos (password corta, username corto, email inválido…). |

### 3. `POST /api/v1/auth/login` — iniciar sesión

Endpoint OAuth2 con `Content-Type: application/x-www-form-urlencoded`. Acepta **username o email** en el campo `username`:

```bash

curl -X POST http://localhost:8000/api/v1/auth/login \

  -H "Content-Type: application/x-www-form-urlencoded" \

  -d "username=ana&password=secret123"

```

`200 OK` — `Token` (ejemplo acortado; un token real tiene firma):

```json

{

  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiZXhwIjoxNzU3Mjk2MDAwfQ.s3cr3tS1gn4tur3",

  "token_type": "bearer"

}

```

| Código | Situación |

| --- | --- |

| `401` | Credenciales inválidas (con `WWW-Authenticate: Bearer`). |

| `422` | Faltan los campos `username` o `password`. |

### 4. `GET /api/v1/users/me` — perfil del usuario autenticado

```bash

curl http://localhost:8000/api/v1/users/me -H "Authorization: Bearer <TOKEN>"

```

`200 OK` — `UserRead` (ver endpoint 2). `401` si el token falta, expiró o el usuario está desactivado.

### 5. `GET /api/v1/users` — listar usuarios

Query params opcionales: `skip` (≥ 0, por defecto 0) y `limit` (1–100, por defecto 50).

```bash

curl "http://localhost:8000/api/v1/users?skip=0&limit=10"

```

`200 OK` — lista de `UserRead`.

### 6. `GET /api/v1/users/{user_id}` — perfil de un usuario

```bash

curl http://localhost:8000/api/v1/users/1

```

`200 OK` — `UserRead`. `404` (`"Usuario no encontrado"`) si no existe.

### 7. `PUT /api/v1/users/{user_id}` — actualizar tu propio perfil

Solo puedes editar tu propio usuario (`403` en otro caso). Campos permitidos: `display_name`, `bio`, `avatar_url`.

```bash

curl -X PUT http://localhost:8000/api/v1/users/1 \

  -H "Authorization: Bearer <TOKEN>" \

  -H "Content-Type: application/json" \

  -d '{"display_name":"Ana García","bio":"Cinefila"}'

```

`200 OK` — `UserRead` actualizado.

| Código | Situación |

| --- | --- |

| `403` | Intentas modificar otro usuario. |

| `404` | El usuario no existe. |

### 8. `DELETE /api/v1/users/{user_id}` — desactivar tu propio usuario

`204 No Content`. Deja `is_active = false`. Igual que el PUT: solo tu propio `user_id` (`403` si no coincide).

### 9. `POST /api/v1/clubs` — crear un club

El usuario autenticado queda registrado automáticamente como `OWNER` en `memberships`.

```bash

curl -X POST http://localhost:8000/api/v1/clubs \

  -H "Authorization: Bearer <TOKEN>" \

  -H "Content-Type: application/json" \

  -d '{"name":"Fans del cine","description":"Comunidad para hablar de películas","visibility":"PUBLIC"}'

```

`201 Created` — `ClubRead`:

```json

{

  "id": 1,

  "name": "Fans del cine",

  "description": "Comunidad para hablar de películas",

  "owner_id": 1,

  "visibility": "PUBLIC",

  "is_active": true,

  "created_at": "2026-09-06T12:05:00",

  "updated_at": "2026-09-06T12:05:00"

}

```

| Código | Situación |

| --- | --- |

| `409` | Ya existe un club con ese nombre. |

| `422` | `name` con menos de 3 caracteres. |

### 10. `GET /api/v1/clubs` — listar clubes

```bash

curl "http://localhost:8000/api/v1/clubs?skip=0&limit=50"

```

`200 OK` — lista de `ClubRead`.

### 11. `GET /api/v1/clubs/{club_id}` — detalle de un club

```bash

curl http://localhost:8000/api/v1/clubs/1

```

`200 OK` — `ClubRead`. `404` (`"Club no encontrado"`) si no existe.

### 12. `PUT /api/v1/clubs/{club_id}` — editar un club

Requiere ser `OWNER` o `ADMIN` del club (`403` si no). Campos: `name`, `description`, `visibility`.

```bash

curl -X PUT http://localhost:8000/api/v1/clubs/1 \

  -H "Authorization: Bearer <TOKEN>" \

  -H "Content-Type: application/json" \

  -d '{"description":"Comunidad actualizada"}'

```

`200 OK` — `ClubRead`. Errores: `403` (permisos), `404` (club), `409` (nombre duplicado).

### 13. `DELETE /api/v1/clubs/{club_id}` — desactivar un club

Solo `OWNER` (`403` si eres `ADMIN`/`MEMBER`). `204 No Content`. Deja `is_active = false`.

### 14. `POST /api/v1/clubs/{club_id}/members` — unirse a un club

```bash

curl -X POST http://localhost:8000/api/v1/clubs/1/members \

  -H "Authorization: Bearer <TOKEN>"

```

`201 Created` — `MembershipRead`:

```json

{

  "id": 2,

  "user_id": 3,

  "club_id": 1,

  "role": "MEMBER",

  "joined_at": "2026-09-06T12:10:00"

}

```

| Código | Situación |

| --- | --- |

| `403` | El club es `PRIVATE` (requiere flujo de invitación/solicitud). |

| `404` | El club no existe. |

| `409` | El usuario ya pertenece al club. |

### 15. `GET /api/v1/clubs/{club_id}/members` — miembros de un club

```bash

curl http://localhost:8000/api/v1/clubs/1/members

```

`200 OK` — lista de `MembershipRead`. `404` si el club no existe.

### 16. `GET /api/v1/users/{user_id}/clubs` — clubes de un usuario

```bash

curl http://localhost:8000/api/v1/users/1/clubs

```

`200 OK` — lista de `MembershipRead`. `404` si el usuario no existe.

### 17. `PATCH /api/v1/clubs/{club_id}/members/{user_id}/role` — cambiar rol

Solo el `OWNER` del club puede cambiar roles (`403` si no). Body: `{"role": "ADMIN" | "MEMBER"}`.

```bash

curl -X PATCH http://localhost:8000/api/v1/clubs/1/members/3/role \

  -H "Authorization: Bearer <TOKEN>" \

  -H "Content-Type: application/json" \

  -d '{"role":"ADMIN"}'

```

`200 OK` — `MembershipRead` con el nuevo rol.

| Código | Situación |

| --- | --- |

| `400` | Intentas cambiar el rol del `OWNER` o asignar `OWNER` (transferencia de propiedad no implementada). |

| `403` | El solicitante no es `OWNER`. |

| `404` | La membresía no existe. |

### 18. `DELETE /api/v1/clubs/{club_id}/members/{user_id}` — salir o expulsar

- Si `user_id` es el propio usuario autenticado, abandona el club.

- Si es otro usuario, requiere `OWNER` o `ADMIN` (expulsión).

`204 No Content`.

| Código | Situación |

| --- | --- |

| `400` | El `OWNER` intenta salir sin transferir/eliminar el club. |

| `403` | Permisos insuficientes para expulsar. |

| `404` | Membresía no encontrada. |

### 19. `POST /api/v1/watch-rooms` — crear una sala

Público (sin token); identifica al anfitrión por `hostUserId`. El anfitrión se registra como participante `HOST` con su `display_name` (o username). `movieId` es el UUID público del catálogo.

```bash

curl -X POST http://localhost:8000/api/v1/watch-rooms \

  -H "Content-Type: application/json" \

  -d '{"movieId":"550e8400-e29b-41d4-a716-446655440000","hostUserId":1,"clubId":1}'

```

`201 Created` — `WatchRoomCreated`; `code` se genera aleatoriamente con formato `ASTRA-XXXX`:

```json

{

  "id": "f0b3c4a1-2a1b-4c3d-8e9f-000000000001",

  "code": "ASTRA-1234",

  "movieId": "550e8400-e29b-41d4-a716-446655440000",

  "status": "WAITING"

}

```

| Código | Situación |

| --- | --- |

| `404` | El usuario anfitrión o el club referenciado no existen. |

| `422` | `movieId` o `hostUserId` faltantes/inválidos. |

### 20. `GET /api/v1/watch-rooms/{code}` — detalle de una sala

```bash

curl http://localhost:8000/api/v1/watch-rooms/ASTRA-1234

```

`200 OK` — `WatchRoomRead` (igual que el anterior más `participants`):

```json

{

  "id": "f0b3c4a1-2a1b-4c3d-8e9f-000000000001",

  "code": "ASTRA-1234",

  "movieId": "550e8400-e29b-41d4-a716-446655440000",

  "status": "WAITING",

  "participants": [

    {"userId": 1, "nickname": "Ana", "role": "HOST"}

  ]

}

```

`404` (`"Sala no encontrada"`) si el código no existe.

### 21. `POST /api/v1/watch-rooms/{code}/join` — unirse a una sala

```bash

curl -X POST http://localhost:8000/api/v1/watch-rooms/ASTRA-1234/join \

  -H "Content-Type: application/json" \

  -d '{"userId":3,"nickname":"Luis"}'

```

`200 OK` — `WatchRoomJoinResult`:

```json

{

  "roomId": "f0b3c4a1-2a1b-4c3d-8e9f-000000000001",

  "joined": true

}

```

| Código | Situación |

| --- | --- |

| `404` | Sala no encontrada o usuario inexistente. |

| `409` | El usuario ya participa en la sala. |

### 22. `DELETE /api/v1/watch-rooms/{code}/participants/{user_id}` — retirar a un participante

```bash

curl -X DELETE http://localhost:8000/api/v1/watch-rooms/ASTRA-1234/participants/3

```

`204 No Content`.

| Código | Situación |

| --- | --- |

| `404` | Sala o participante no encontrado. |

| `409` | El anfitrión (`HOST`) no puede salir de su propia sala. |

### Flujo típico para crear una comunidad

1. Registra el usuario (`POST /auth/register`) y obtén un JWT (`POST /auth/login`).

2. Crea el club autenticado con `POST /clubs`; el usuario queda como `OWNER`.

3. Otros usuarios se unen con `POST /clubs/{id}/members` si el club es `PUBLIC`.

4. El `OWNER` asigna `ADMIN` o `MEMBER` con el `PATCH` de rol; los administradores pueden editar el club y expulsar miembros.

5. Crea una watch room asociada opcionalmente al club. Para reproducción sincronizada o chat, integra el servicio realtime separado.

>>>>>>> b3060d44607c468f3f643124be49e68466967a08