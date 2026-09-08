# Community & Watch Party Service

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
.venv\Scripts\Activate.ps1
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

```bash
docker compose pull
docker compose up -d
```

No exponga MySQL; publique Community detrás de TLS/proxy y conserve copias de seguridad del volumen.
