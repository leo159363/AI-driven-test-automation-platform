# API Document: Authentication

source_type: api_doc

Endpoint: `POST /api/login`

Request body:

```json
{
  "username": "tester",
  "password": "Passw0rd!"
}
```

Expected responses:

- `200 OK` with `token` and `user`.
- `400 Bad Request` when required fields are missing.
- `401 Unauthorized` when credentials are invalid.
- `423 Locked` when the account is temporarily locked.
