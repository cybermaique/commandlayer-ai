class CommandValidator:
    @staticmethod
    def validate(command):
        if not isinstance(command.requested_by, str) or not command.requested_by.strip():
            raise ValueError("requested_by is required")

        if command.payload is None:
            command.payload = {}

        if not isinstance(command.payload, dict):
            raise ValueError("Payload must be an object")

        has_action = bool(command.action)
        has_raw_text = bool(command.raw_text)

        if not has_action and not has_raw_text:
            raise ValueError("Action or raw_text is required")

        if command.action is not None and (not isinstance(command.action, str) or not command.action.strip()):
            raise ValueError("Action must be a non-empty string")

        if command.raw_text is not None and (not isinstance(command.raw_text, str) or not command.raw_text.strip()):
            raise ValueError("raw_text must be a non-empty string")