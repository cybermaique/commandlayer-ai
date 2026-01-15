from enum import Enum


class AssetType(str, Enum):
    VEHICLE = "vehicle"
    DEVICE = "device"
    TEAM = "team"
    GENERIC = "generic"


class TaskStatus(str, Enum):
    SCHEDULED = "scheduled"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class CommandStatus(str, Enum):
    RECEIVED = "received"
    EXECUTED = "executed"
    FAILED = "failed"
