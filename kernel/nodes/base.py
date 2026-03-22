from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any, Dict

from kernel.nodes.errors import (
    NodeExecutionError,
    PolicyBlockedError,
    TerminalNodeError,
)
from kernel.nodes.result import (
    NodeObservation,
    NodeResult,
    ObservationCategory,
)

class BaseNode(ABC):
    """
    Base class for all executable OpsIQ nodes.

    Subclasses implement '_run(state)' and return a NodeResult.
    The public 'run(state)' method wraps execution with:
      - precondition validation
      - timing
      - standardized exception handling
      - standard metric emission

    Design rule:
    Nodes should not mutate shared kernel state directly.
    They should return a NodeResult containing a state_patch.
    """

    name: str = "base_node"

    async def run(self, state: Dict[str, Any]) -> NodeResult:
        """
        Public execution wrapper used by the kernel/runtime.

        This method:
        1. validates node preconditions
        2. calls the node's implementation
        3. appends standard metrics
        4. normalizes typed and untyped exceptions into NodeResult
        """
        start = time.perf_counter()

        try:
            self.validate_preconditions(state)
            result = await self._run(state)

            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
            result.metrics.setdefault("node_name", self.name)
            result.metrics.setdefault("elapsed_ms", elapsed_ms)
            result.metrics.setdefault("result_status", result.status.value)

            return result

        except NodeExecutionError as exc:
            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
            return self._result_from_node_error(exc=exc, elapsed_ms=elapsed_ms)

        except Exception as exc:
            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)

            wrapped = TerminalNodeError(
                message=f"Unhandled exception in node '{self.name}'",
                cause=exc,
            )
            return self._result_from_node_error(exc=wrapped, elapsed_ms=elapsed_ms)

    def validate_preconditions(self, state: Dict[str, Any]) -> None:
        """
        Override in subclasses when the node requires specific fields
        to exist in state before running.

        Raise a NodeExecutionError subclass if preconditions are not met.
        """
        return None

    @abstractmethod
    async def _run(self, state: Dict[str, Any]) -> NodeResult:
        """
        Subclasses implement actual node behavior here.

        This method should:
        - read from the provided state
        - perform bounded node logic
        - return a NodeResult
        - avoid mutating shared state directly
        """
        raise NotImplementedError

    def _result_from_node_error(self, exc: NodeExecutionError, elapsed_ms: float) -> NodeResult:
        """
        Convert a typed node exception into a standardized NodeResult.
        """
        observations = [
            NodeObservation(
                name="node_exception",
                value=str(exc),
                category=ObservationCategory.SYSTEM,
                message=f"Node '{self.name}' raised {exc.code.value}",
                tags=["error", exc.code.value],
                confidence=None,
            )
        ]

        metrics = {
            "node_name": self.name,
            "elapsed_ms": elapsed_ms,
            "error_code": exc.code.value,
            "retryable": exc.retryable,
        }

        if isinstance(exc, PolicyBlockedError):
            return NodeResult.blocked(
                errors=[str(exc)],
                observations=observations,
                metrics=metrics,
            )

        return NodeResult.failed(
            errors=[str(exc)],
            observations=observations,
            metrics=metrics,
        )