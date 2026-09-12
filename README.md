# Cinema Club Online — Community Service

Microservicio REST de comunidad para perfiles sociales, clubes, membresías y salas de *watch party*.

## Architecture

El servicio está implementado con **Python**, **FastAPI**, **Pydantic v2**, **SQLAlchemy 2** y **MySQL**. La aplicación se compone de las siguientes capas:

```text
app/
├── api/           # Router principal, rutas HTTP y dependencias
├── core/          # Configuración y validación JWT
├── database/      # Base SQLAlchemy y sesiones
├── models/        # Modelos ORM: User, Club, Membership y WatchRoom
├── repositories/  # Acceso a datos
├── schemas/       # Contratos Pydantic de request/response
└── services/      # Reglas de negocio y permisos
```

La API registra todos los routers con el prefijo base **`/api/v1`**. Por ejemplo, una instancia local expuesta en el puerto 8000 respondería en `http://localhost:8000/api/v1`.

La persistencia usa MySQL mediante `DATABASE_URL` o, cuando no se define, mediante `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_DATABASE`, `MYSQL_USER` y `MYSQL_PASSWORD`.

La identidad depende del servicio externo **identity-service**. Este servicio no registra usuarios, no recibe contraseñas y no emite tokens. Valida JWT con `JWT_SECRET`, `JWT_ALGORITHM` (por defecto `HS256`) y `JWT_ISSUER` (por defecto `identity-service`). El UUID del claim `sub` se almacena en `users.identity_user_id`; el primer acceso autenticado puede crear el perfil local.

Los UUID de películas recibidos por las salas son referencias al catálogo externo; no hay una clave foránea a otro microservicio.

## Configuration

| Variable | Uso |
| --- | --- |
| `DATABASE_URL` | URL completa de SQLAlchemy. Tiene prioridad sobre la configuración `MYSQL_*`. |
| `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_DATABASE`, `MYSQL_USER`, `MYSQL_PASSWORD` | Configuración de MySQL cuando no se usa `DATABASE_URL`. |
| `JWT_SECRET` | Secreto compartido para validar los JWT de identity-service. |
| `JWT_ALGORITHM` | Algoritmo JWT; el valor predeterminado es `HS256`. |
| `JWT_ISSUER` | Emisor exigido en el JWT; el valor predeterminado es `identity-service`. |

## API Endpoints

Base URL: `{{base_url}}`  
Prefijo de negocio: `{{base_url}}/api/v1`

Las rutas que reciben JSON requieren el header `Content-Type: application/json`. Los endpoints protegidos se indican en la columna **Auth** y usan el header descrito en [Authentication](#authentication).

### Health

| Método | Ruta | Auth | Descripción | Parámetros | Body |
| --- | --- | --- | --- | --- | --- |
| `GET` | `/api/v1/health` | No | Comprueba la disponibilidad del servicio. | — | — |

Respuesta: `{"status":"ok","service":"community-service"}`.

### Users

| Método | Ruta | Auth | Descripción | Parámetros | Body |
| --- | --- | --- | --- | --- | --- |
| `GET` | `/api/v1/users/me` | Sí | Devuelve el perfil del usuario identificado por el JWT. | — | — |
| `GET` | `/api/v1/users` | No | Lista usuarios paginados. | Query: `skip` entero ≥ 0 (predeterminado `0`), `limit` entero 1–100 (predeterminado `50`). | — |
| `GET` | `/api/v1/users/{user_id}` | No | Obtiene un usuario por identificador. | Path: `user_id` entero. | — |
| `PUT` | `/api/v1/users/{user_id}` | Sí; solo el propio usuario | Actualiza el perfil. | Path: `user_id` entero. | JSON opcional: `display_name` (máx. 100), `bio` (máx. 500), `avatar_url` (máx. 500). |
| `DELETE` | `/api/v1/users/{user_id}` | Sí; solo el propio usuario | Desactiva el usuario (`is_active=false`). Devuelve `204`. | Path: `user_id` entero. | — |

Modelo de respuesta `UserRead`: `id`, `identity_user_id`, `username`, `email`, `display_name`, `bio`, `avatar_url`, `is_active`, `created_at`, `updated_at`.

Ejemplo de actualización:

```json
{
  "display_name": "Ana García",
  "bio": "Amante del cine",
  "avatar_url": "https://example.com/ana.jpg"
}
```

### Clubs

| Método | Ruta | Auth | Descripción | Parámetros | Body |
| --- | --- | --- | --- | --- | --- |
| `POST` | `/api/v1/clubs` | Sí | Crea un club y asigna al solicitante el rol `OWNER`. Devuelve `201`. | — | `name` requerido (3–120), `description` opcional, `visibility` opcional: `PUBLIC` o `PRIVATE` (por defecto `PUBLIC`). |
| `GET` | `/api/v1/clubs` | No | Lista los clubes activos, paginados. | Query: `skip` entero ≥ 0 (predeterminado `0`), `limit` entero 1–100 (predeterminado `50`). | — |
| `GET` | `/api/v1/clubs/{club_id}` | No | Obtiene un club por ID. | Path: `club_id` entero. | — |
| `PUT` | `/api/v1/clubs/{club_id}` | Sí; `OWNER` o `ADMIN` | Actualiza un club activo. | Path: `club_id` entero. | JSON opcional: `name` (3–120), `description`, `visibility` (`PUBLIC` o `PRIVATE`). |
| `DELETE` | `/api/v1/clubs/{club_id}` | Sí; solo `OWNER` | Desactiva el club. Devuelve `204`. | Path: `club_id` entero. | — |

Ejemplo de creación:

```json
{
  "name": "Cine Clásico",
  "description": "Comunidad para ver clásicos",
  "visibility": "PUBLIC"
}
```

Modelo de respuesta `ClubRead`: `id`, `name`, `description`, `owner_id`, `visibility`, `is_active`, `created_at`, `updated_at`.

### Memberships

| Método | Ruta | Auth | Descripción | Parámetros | Body |
| --- | --- | --- | --- | --- | --- |
| `POST` | `/api/v1/clubs/{club_id}/members` | Sí | Inscribe al usuario actual como `MEMBER` en un club público. Devuelve `201`. | Path: `club_id` entero. | — |
| `GET` | `/api/v1/clubs/{club_id}/members` | No | Lista las membresías de un club. | Path: `club_id` entero. | — |
| `GET` | `/api/v1/users/{user_id}/clubs` | No | Lista las membresías de un usuario. | Path: `user_id` entero. | — |
| `PATCH` | `/api/v1/clubs/{club_id}/members/{user_id}/role` | Sí; solo `OWNER` | Cambia el rol de una membresía que no sea del propietario. | Path: `club_id` y `user_id`, enteros. | `role`: `ADMIN` o `MEMBER`. Solicitar `OWNER` es rechazado. |
| `DELETE` | `/api/v1/clubs/{club_id}/members/{user_id}` | Sí | El propio miembro puede salir; para retirar a otra persona se requiere `OWNER` o `ADMIN`. Devuelve `204`. | Path: `club_id` y `user_id`, enteros. | — |

Modelo de respuesta `MembershipRead`: `id`, `user_id`, `club_id`, `role` (`OWNER`, `ADMIN` o `MEMBER`) y `joined_at`.

Ejemplo para cambiar el rol:

```json
{
  "role": "ADMIN"
}
```

### Watch Rooms

| Método | Ruta | Auth | Descripción | Parámetros | Body |
| --- | --- | --- | --- | --- | --- |
| `POST` | `/api/v1/watch-rooms` | Sí | Crea una sala y registra al solicitante como participante `HOST`. Si se asocia a un club, el solicitante debe pertenecer a él. Devuelve `201`. | — | `movieId` UUID requerido; `clubId` entero positivo opcional. También se aceptan los alias de entrada `movie_id` y `club_id`. |
| `GET` | `/api/v1/watch-rooms/{code}` | No | Obtiene una sala y sus participantes. La búsqueda normaliza el código a mayúsculas. | Path: `code` cadena. | — |
| `POST` | `/api/v1/watch-rooms/{code}/join` | Sí | Agrega al solicitante como participante `VIEWER`. En una sala de club exige membresía. | Path: `code` cadena. | `nickname` requerido, de 1 a 100 caracteres. |
| `DELETE` | `/api/v1/watch-rooms/{code}/participants/{user_id}` | Sí | Retira a un participante. Puede hacerlo el propio participante, el anfitrión, o un `OWNER`/`ADMIN` del club asociado. Devuelve `204`. | Path: `code` cadena y `user_id` entero. | — |

Ejemplo de creación:

```json
{
  "movieId": "550e8400-e29b-41d4-a716-446655440000",
  "clubId": 1
}
```

Ejemplo para unirse:

```json
{
  "nickname": "Carlos"
}
```

`POST /watch-rooms` responde `WatchRoomCreated` con `id`, `code`, `movieId` y `status`. `GET /watch-rooms/{code}` añade `participants`, cuyos elementos contienen `userId`, `nickname` y `role` (`HOST` o `VIEWER`). La unión responde `{"roomId":"<uuid>","joined":true}`.

### FastAPI documentation routes

FastAPI expone además las siguientes rutas sin autenticación:

| Método | Ruta | Descripción |
| --- | --- | --- |
| `GET` | `/openapi.json` | Esquema OpenAPI generado automáticamente. |
| `GET` | `/docs` | Interfaz Swagger UI. |
| `GET` | `/redoc` | Interfaz ReDoc. |

Los errores de negocio usan el formato estándar de FastAPI: `{"detail":"<mensaje>"}`. Los endpoints protegidos pueden devolver `401` con `WWW-Authenticate: Bearer`; las validaciones de parámetros o cuerpos devuelven `422`.

## Authentication

Los endpoints protegidos usan JWT Bearer. Configure la variable de Postman `{{token}}` con un token emitido por el **identity-service** externo y envíe:

```http
Authorization: Bearer {{token}}
```

El token debe poder verificarse con la configuración local y contener `sub` (UUID), `exp` e `iss`. Se usan opcionalmente `email`, `username`, `preferred_username`, `display_name` o `name` para enlazar o crear el perfil local. La ruta OAuth2 declarada para documentación apunta a `identity-service/api/auth/login`; no existe un endpoint de login en este repositorio.

## Postman Collection

Se generó la colección **`Community_Watch_Party_API.postman_collection.json`** para probar las rutas actuales. La colección utiliza la variable:

```text
{{base_url}}
```

Asigne, por ejemplo, `http://IP_DE_LA_MAQUINA_VIRTUAL:PUERTO` para cambiar rápidamente la IP y el puerto de la máquina virtual. También incluye `{{token}}`, `{{user_id}}`, `{{club_id}}` y `{{room_code}}` como variables auxiliares.

## Known Limitations

- El login y la emisión de JWT dependen de identity-service y no están implementados en este repositorio.
- Los clubes `PRIVATE` no tienen un flujo de invitación ni de solicitud de acceso; intentar unirse devuelve `403`.
- No hay transferencia de propiedad de clubes: no se puede asignar el rol `OWNER` mediante la API, y el propietario no puede abandonar el club.
- El servicio no implementa chat, WebSockets ni sincronización de reproducción de la watch party.
