# Web Console v1.0.0 Manual Test Guide

## Run full stack

```bash
docker compose up -d --build
```

Open:
- Frontend: http://localhost:3000
- Backend docs: http://localhost:8000/docs

## Configure the console

1. Open the console.
2. Set Base URL to `http://localhost:8000`.
3. Select Auth mode:
   - `off` for public mode
   - `api_key` for key-protected mode
4. If using API key mode, set header name to `X-API-Key` (or your configured name) and paste a key.
5. Optionally enable “Remember for session only”.
6. Click **Test Connection** and confirm `ok`.

## Test cases

### AUTH_MODE=off

1. Ensure backend environment has `AUTH_MODE=off`.
2. Execute a direct command:
   - requested_by: `web-console`
   - action: `assign_task`
   - payload: `{ "asset_id": "<asset-id>", "task_id": "<task-id>" }`
3. Expect `200` response with `success` or `noop`.
4. Confirm Recent activity shows the execution.

### AUTH_MODE=api_key

1. Ensure backend environment has `AUTH_MODE=api_key` and at least one API key.
2. Missing key:
   - Select Auth mode `api_key` but leave API key empty.
   - Execute a command.
   - Expect `401` with `error_code=unauthorized`.
3. Invalid key:
   - Use an invalid key value.
   - Expect `401` with `error_code=unauthorized`.
4. Readonly role restriction:
   - Use a `readonly` key.
   - Execute `assign_task`.
   - Expect `403` with `error_code=forbidden`.
5. Rate limit:
   - Rapidly execute the same command until rate limited.
   - Expect `429` with `error_code=rate_limited`.
6. Successful command:
   - Use a `runner` or `admin` key.
   - Execute `assign_task`.
   - Expect `200` with `success` or `noop`.
7. Logs visibility:
   - In Recent activity, confirm rows show status, action, api key name, role.
   - Open details modal and confirm `resolution.auth` and `api_key_id` appear.
