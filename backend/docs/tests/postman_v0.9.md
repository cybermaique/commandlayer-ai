# Postman tests - v0.9.0 (API key auth + RBAC + rate limiting)

## Preconditions
- Set `AUTH_MODE=api_key`.
- (Optional) Set `AUTH_HEADER_NAME` (default `X-API-Key`).
- (Optional) Set `RATE_LIMIT_PER_MINUTE` (default `60`).
- Ensure database migrations are applied.

Start services:
```bash
docker compose up -d --build
```

Apply migrations:
```bash
docker compose exec backend alembic upgrade head
```

## Create API keys
Create a runner key:
```bash
docker compose exec backend python -m app.scripts.create_api_key --name "postman-runner" --role runner
```

Create a readonly key (for 403 test):
```bash
docker compose exec backend python -m app.scripts.create_api_key --name "postman-readonly" --role readonly
```

Copy the plaintext key printed by the command (it is shown only once).

## Test A: Missing key (401)
```bash
curl -X POST http://localhost:8000/commands \
  -H 'Content-Type: application/json' \
  -d '{
    "action": "assign_task",
    "payload": {
      "asset_id": "11111111-1111-1111-1111-111111111111",
      "task_id": "22222222-2222-2222-2222-222222222222"
    }
  }'
```
Expected: `401` with `error_code=unauthorized`.

## Test B: Invalid key (401)
```bash
curl -X POST http://localhost:8000/commands \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: invalid-key' \
  -d '{
    "action": "assign_task",
    "payload": {
      "asset_id": "11111111-1111-1111-1111-111111111111",
      "task_id": "22222222-2222-2222-2222-222222222222"
    }
  }'
```
Expected: `401` with `error_code=unauthorized`.

## Test C: Forbidden role (403)
```bash
curl -X POST http://localhost:8000/commands \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: <READONLY_KEY>' \
  -d '{
    "action": "assign_task",
    "payload": {
      "asset_id": "11111111-1111-1111-1111-111111111111",
      "task_id": "22222222-2222-2222-2222-222222222222"
    }
  }'
```
Expected: `403` with `error_code=forbidden`.

## Test D: Rate limit (429)
Run a quick loop using a valid runner key:
```bash
for i in $(seq 1 70); do
  curl -s -o /dev/null -w "%{http_code}\n" \
    -X POST http://localhost:8000/commands \
    -H 'Content-Type: application/json' \
    -H 'X-API-Key: <RUNNER_KEY>' \
    -d '{
      "action": "assign_task",
      "payload": {
        "asset_id": "11111111-1111-1111-1111-111111111111",
        "task_id": "22222222-2222-2222-2222-222222222222"
      }
    }'
done
```
Expected: after `RATE_LIMIT_PER_MINUTE`, responses return `429` with `error_code=rate_limited`.

## Test E: Success (200)
```bash
curl -X POST http://localhost:8000/commands \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: <RUNNER_KEY>' \
  -d '{
    "action": "assign_task",
    "payload": {
      "asset_id": "11111111-1111-1111-1111-111111111111",
      "task_id": "22222222-2222-2222-2222-222222222222"
    }
  }'
```
Expected: `200` with `status` `success` or `noop`.

## SQL verification
Check api_keys:
```sql
select id, name, role, active, created_at
from api_keys
order by created_at desc
limit 5;
```

Check command_logs api_key_id and auth metadata:
```sql
select id, api_key_id, intent_json
from command_logs
order by created_at desc
limit 5;
```
Expected in `intent_json.resolution.auth`:
- `mode: "api_key"`
- `api_key_name`: string
- `role`: `admin|runner|readonly`
