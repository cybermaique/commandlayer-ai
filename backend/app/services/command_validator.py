import uuid


class CommandValidator:
    ALLOWED_ACTIONS = {"assign_task"}

    @staticmethod
    def validate_request(command) -> None:
        if not isinstance(command.requested_by, str) or not command.requested_by.strip():
            raise ValueError("requested_by is required")

        if command.payload is not None and not isinstance(command.payload, dict):
            raise ValueError("Payload must be an object")

        has_action = bool(command.action)
        has_raw_text = bool(command.raw_text)

        if not has_action and not has_raw_text:
            raise ValueError("Action or raw_text is required")

        if command.action is not None and (
            not isinstance(command.action, str) or not command.action.strip()
        ):
            raise ValueError("Action must be a non-empty string")

        if command.raw_text is not None and (
            not isinstance(command.raw_text, str) or not command.raw_text.strip()
        ):
            raise ValueError("raw_text must be a non-empty string")

    @staticmethod
    def validate_action_payload(action: str, payload: dict) -> None:
        if action not in CommandValidator.ALLOWED_ACTIONS:
            raise ValueError("Unsupported action")

        if not isinstance(payload, dict):
            raise ValueError("Payload must be an object")

        if action == "assign_task":
            required_fields = {"asset_id", "task_id"}
            extra_fields = set(payload.keys()) - required_fields
            if extra_fields:
                raise ValueError("Payload has unsupported fields")

            asset_id = payload.get("asset_id")
            task_id = payload.get("task_id")

            if not isinstance(asset_id, str) or not asset_id.strip():
                raise ValueError("asset_id is required")
            if not isinstance(task_id, str) or not task_id.strip():
                raise ValueError("task_id is required")

            try:
                uuid.UUID(asset_id)
                uuid.UUID(task_id)
            except ValueError as exc:
                raise ValueError(
                    "asset_id and task_id must be valid UUIDs"
                ) from exc
