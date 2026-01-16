# Postman test plan — v0.6

## Pré-requisitos

* Definir `INTENT_RESOLUTION_MODE=llm`
* Definir `OPENAI_API_KEY`
* `docker compose up -d --build`

---

## A) Direct mode continua funcionando

POST `/commands`

```json
{
  "action": "assign_task",
  "payload": {
    "asset_id": "33333333-3333-3333-3333-333333333333",
    "task_id": "44444444-4444-4444-4444-444444444444"
  },
  "requested_by": "local-test"
}
```

Esperado: 200 success/noop (dependendo se existe)

---

## B) LLM raw_text cria assignment (novo)

POST `/commands`

```json
{
  "raw_text": "Assign task: asset_id=33333333-3333-3333-3333-333333333333 task_id=44444444-4444-4444-4444-444444444444",
  "requested_by": "local-test"
}
```

Esperado:

* 200
* action `assign_task`
* result success/noop
* (opcional) response inclui `resolution.provider/model/confidence`

---

## C) LLM raw_text repetido deve dar noop

Repetir B.
Esperado: 200 + noop + already_exists true

---

## D) Raw text inválido

POST `/commands`

```json
{
  "raw_text": "assign_task asset_id=33333333-3333-3333-3333-333333333333",
  "requested_by": "local-test"
}
```

Esperado:

* 422
* `error_code: intent_resolution_failed` (ou equivalente)
* response com erros

---

## E) Sem api key

Remover `OPENAI_API_KEY` e repetir B.
Esperado:

* 503 (ou 500 se não tratou — mas objetivo é 503)
* msg: provider_unavailable