from dataclasses import dataclass
from enum import Enum
from typing import Optional


class NodeErrorCode(str, Enum):
    INVALID_INPUT = "invalid_input"
    MISSING_REQUIRED_STATE = "missing_required_state"
    POLICY_BLOCKED = "policy_blocked"
    RETRYABLE_FAILURE = "retryable_failure"
    TERMINAL_FAILURE = "terminal_failure"
    EXECUTION_TIMEOUT = "execution_timeout"
    DEPENDENCY_FAILURE = "dependency_failure"
    UNKNOWN = "unknown"


@dataclass
class NodeExecutionError(Exception):
    """
    Base exception for all node-related failures.

    These exceptions are raised inside node implementations and then
    normalized by the BaseNode runtime wrapper into a NodeResult.
    """
    message: str
    code: NodeErrorCode = NodeErrorCode.UNKNOWN
    retryable: bool = False
    cause: Optional[Exception] = None

    def __str__(self) -> str:
        return f"{self.code.value}: {self.message}"


class MissingRequiredStateError(NodeExecutionError):
    def __init__(self, message: str):
        super().__init__(
            message=message,
            code=NodeErrorCode.MISSING_REQUIRED_STATE,
            retryable=False,
        )


class InvalidInputError(NodeExecutionError):
    def __init__(self, message: str):
        super().__init__(
            message=message,
            code=NodeErrorCode.INVALID_INPUT,
            retryable=False,
        )


class PolicyBlockedError(NodeExecutionError):
    def __init__(self, message: str):
        super().__init__(
            message=message,
            code=NodeErrorCode.POLICY_BLOCKED,
            retryable=False,
        )


class RetryableNodeError(NodeExecutionError):
    def __init__(self, message: str, cause: Optional[Exception] = None):
        super().__init__(
            message=message,
            code=NodeErrorCode.RETRYABLE_FAILURE,
            retryable=True,
            cause=cause,
        )


class TerminalNodeError(NodeExecutionError):
    def __init__(self, message: str, cause: Optional[Exception] = None):
        super().__init__(
            message=message,
            code=NodeErrorCode.TERMINAL_FAILURE,
            retryable=False,
            cause=cause,
        )


class NodeTimeoutError(NodeExecutionError):
    def __init__(self, message: str = "Node execution timed out"):
        super().__init__(
            message=message,
            code=NodeErrorCode.EXECUTION_TIMEOUT,
            retryable=True,
        )


class DependencyFailureError(NodeExecutionError):
    def __init__(self, message: str, retryable: bool = False):
        super().__init__(
            message=message,
            code=NodeErrorCode.DEPENDENCY_FAILURE,
            retryable=retryable,
        )