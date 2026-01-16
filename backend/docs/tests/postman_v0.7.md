# Postman Manual Tests — v0.7

## Preconditions

- `INTENT_RESOLUTION_MODE=llm`.
- First run with `RAG_MODE=off`, then with `RAG_MODE=lite`.
- `OPENAI_API_KEY` configured.
- `docker compose up -d --build`.

## Test A — Direct mode (action/payload)

**Request**

- Method: `POST`
- URL: `http://localhost:8000/commands`
- Body (JSON):

```json
{
  "action": "assign_task",
  "payload": {
    "asset_id": "4f6a20d3-0b3e-4df6-9f6e-9c0b1a2d3e4f",
    "task_id": "7a1b2c3d-4e5f-6a7b-8c9d-0e1f2a3b4c5d"
  }
}
```

**Expected**

- `200 OK`.
- `status=success` or `status=noop`.

## Test B — LLM raw_text without RAG

**Setup**

- `RAG_MODE=off`.

**Request**

- Method: `POST`
- URL: `http://localhost:8000/commands`
- Body (JSON):

```json
{
  "raw_text": "Assign task 7a1b2c3d-4e5f-6a7b-8c9d-0e1f2a3b4c5d to asset 4f6a20d3-0b3e-4df6-9f6e-9c0b1a2d3e4f"
}
```

**Expected**

- `200 OK`.
- `status=success` or `status=noop`.

## Test C — LLM raw_text with RAG enabled

**Setup**

- `RAG_MODE=lite`.

**Request**

- Method: `POST`
- URL: `http://localhost:8000/commands`
- Body (JSON):

```json
{
  "raw_text": "Assign task 7a1b2c3d-4e5f-6a7b-8c9d-0e1f2a3b4c5d to asset 4f6a20d3-0b3e-4df6-9f6e-9c0b1a2d3e4f"
}
```

**Expected**

- `200 OK`.
- `status=success` or `status=noop`.
- Audit log contains `rag.enabled=true`.

## Test D — Verify audit log metadata

Run the SQL query below and confirm `intent_json` contains `rag.enabled` and `rag.sources` for the LLM request:

```sql
SELECT id, intent_json
FROM command_logs
ORDER BY id DESC
LIMIT 5;
```

**Expected**

- `intent_json.rag.enabled` is `true` when `RAG_MODE=lite`.
- `intent_json.rag.sources` is a list of `.md` files used.
