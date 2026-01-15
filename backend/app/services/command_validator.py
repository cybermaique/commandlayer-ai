class CommandValidator:
    @staticmethod
    def validate(command):
        if not command.action:
            raise ValueError("Action is required")

        if not isinstance(command.payload, dict):
            raise ValueError("Payload must be an object")
