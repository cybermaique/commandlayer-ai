# Postman Tests — CommandLayer V0.5 (Intent Resolution)

This document defines the **HTTP test scenarios** for CommandLayer **V0.5**.

The goal of V0.5 is to introduce **Intent Resolution** while preserving full backward compatibility with the existing `action + payload` execution model.

All tests below must pass to consider V0.5 complete.

---

## Base URL

```

[http://localhost:8000](http://localhost:8000)

```

Endpoint used in all tests:

```

POST /commands

````

---

## Test Data Prerequisites (Database)

Before running the tests, ensure the following records exist:

### Assets

| asset_id |
|---------|
| `11111111-1111-1111-1111-111111111111` |
| `33333333-3333-3333-3333-333333333333` |

### Tasks

| task_id |
|--------|
| `22222222-2222-2222-2222-222222222222` |
| `44444444-4444-4444-4444-444444444444` |

---

## A) Direct Command — Create Assignment (action + payload)

### Request

```json
{
  "action": "assign_task",
  "payload": {
    "asset_id": "11111111-1111-1111-1111-111111111111",
    "task_id": "22222222-2222-2222-2222-222222222222"
  },
  "requested_by": "local-test"
}
````

### Expected Response

* HTTP `200 OK`
* `status`: `"success"`
* `already_exists`: `false`

Example:

```json
{
  "status": "success",
  "action": "assign_task",
  "result": {
    "assignment_id": "<uuid>",
    "already_exists": false
  }
}
```

---

## B) Direct Command — Repeated (Idempotent / Noop)

### Request

(Same request as A)

```json
{
  "action": "assign_task",
  "payload": {
    "asset_id": "11111111-1111-1111-1111-111111111111",
    "task_id": "22222222-2222-2222-2222-222222222222"
  },
  "requested_by": "local-test"
}
```

### Expected Response

* HTTP `200 OK`
* `status`: `"noop"`
* `already_exists`: `true`

Example:

```json
{
  "status": "noop",
  "action": "assign_task",
  "result": {
    "assignment_id": "<existing_uuid>",
    "already_exists": true
  }
}
```

---

## C) Raw Text Command — Create Assignment

This test validates **Intent Resolution**.

### Request

```json
{
  "raw_text": "assign_task asset_id=33333333-3333-3333-3333-333333333333 task_id=44444444-4444-4444-4444-444444444444",
  "requested_by": "local-test"
}
```

### Expected Response

* HTTP `200 OK`
* `action`: `"assign_task"`
* `status`: `"success"`

Example:

```json
{
  "status": "success",
  "action": "assign_task",
  "result": {
    "assignment_id": "<uuid>",
    "already_exists": false
  }
}
```

---

## D) Raw Text Command — Repeated (Idempotent / Noop)

### Request

(Same request as C)

```json
{
  "raw_text": "assign_task asset_id=33333333-3333-3333-3333-333333333333 task_id=44444444-4444-4444-4444-444444444444",
  "requested_by": "local-test"
}
```

### Expected Response

* HTTP `200 OK`
* `status`: `"noop"`
* `already_exists`: `true`

---

## E) Raw Text Command — Invalid Input

Missing required parameter (`task_id`).

### Request

```json
{
  "raw_text": "assign_task asset_id=33333333-3333-3333-3333-333333333333",
  "requested_by": "local-test"
}
```

### Expected Response

* HTTP `400` or `422`
* Error clearly indicates intent resolution failure

Example:

```json
{
  "error_code": "intent_resolution_failed",
  "errors": [
    "task_id is required"
  ]
}
```

---

## Acceptance Criteria (V0.5)

* Direct `action + payload` execution remains unchanged
* Raw text commands resolve to the same executable intent
* Commands are **idempotent**
* No duplicate assignments are created
* Invalid raw text fails gracefully (no 500 errors)

---

## Notes

* This document serves as **manual regression tests**
* It will be used as the base for automated tests in future versions
* Any breaking change must update this file and bump the version

````

---

## ✅ O que você faz agora (checklist rápido)

1. Criar o arquivo:
   ```bash
   backend/docs/tests/postman_v0.5.md
````

2. Colar exatamente esse conteúdo
3. Commit:

   ```bash
   git add backend/docs/tests/postman_v0.5.md
   git commit -m "docs: add Postman tests for intent resolution (v0.5)"
   ```