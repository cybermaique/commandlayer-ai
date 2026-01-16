# Policies

Supported actions:
- assign_task

Rules:
- Never invent IDs.
- If asset_id and task_id are missing, return an error explaining the missing fields.
- Use only IDs present in the user input or in the provided context.
