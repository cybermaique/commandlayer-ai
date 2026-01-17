# Postman tests - v0.8.0 (Vector RAG)

## Preconditions
- Set `RAG_MODE=vector`.
- Set `OPENAI_API_KEY`.
- Ensure `OPENAI_EMBEDDINGS_MODEL` and `OPENAI_EMBEDDINGS_DIM` match.
- Run KB ingestion before testing.
- If you previously used a `postgres` image without pgvector, recreate the volume.

## Docker commands
Recreate Postgres volume (first time after switching to pgvector image):
```bash
docker compose down -v
docker compose up -d --build
```

Ingest the knowledge base:
```bash
docker compose exec backend python -m app.scripts.ingest_kb
```

Run Postman tests (via Postman collection or curl equivalents below).

## Test A: Direct mode (200)
Request:
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
Expected: `200`, status `success` or `noop`.

## Test B: Vector RAG raw_text without UUIDs (200)
Request:
```bash
curl -X POST http://localhost:8000/commands \
  -H 'Content-Type: application/json' \
  -d '{
    "raw_text": "Assign Task 1 to Agent 1"
  }'
```
Expected: `200`, status `success` or `noop`.

## Test C: RAG_MODE=off same raw_text -> 422 missing_fields
Set `RAG_MODE=off` and restart backend, then:
```bash
curl -X POST http://localhost:8000/commands \
  -H 'Content-Type: application/json' \
  -d '{
    "raw_text": "Assign Task 1 to Agent 1"
  }'
```
Expected: `422` with `error_code=missing_fields`.

## Test D: command_logs rag metadata
Query command_logs for rag metadata:
```sql
select id, intent_json
from command_logs
order by created_at desc
limit 1;
```
Expected in `intent_json.resolution.rag`:
- `enabled: true`
- `mode: "vector"`
- `sources`: array of filenames
- `context_chars`: integer
- `top_k`: integer
- `retrieved_chunks`: integer

## SQL queries
Verify knowledge_chunks table:
```sql
select source, chunk_index, content_hash
from knowledge_chunks
order by source, chunk_index
limit 10;
```

Check total chunks:
```sql
select count(*) from knowledge_chunks;
```
