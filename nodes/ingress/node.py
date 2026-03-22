from typing import Any, Dict

from kernel.nodes.base import BaseNode
from kernel.nodes.errors import InvalidInputError, MissingRequiredStateError
from kernel.nodes.result import NodeResult
from kernel.tasks.task import Objective
from nodes.ingress.schema import IngressEvent, IngressStatePatch


class IngressNode(BaseNode):
    """
    Ingress Node (v0)

    Responsibilities:
    - Validate ingress_event exists in state
    - Parse ingress_event into a typed IngressEvent
    - Normalize input text
    - Derive an Objective from the input
    - Return a typed ingress state patch

    Out of scope:
    - Task creation
    - Routing
    - Planning
    - Execution
    """

    name = "ingress_node"

    def validate_preconditions(self, state: Dict[str, Any]) -> None:
        if "ingress_event" not in state:
            raise MissingRequiredStateError(
                "IngressNode requires 'ingress_event' in state."
            )

    async def _run(self, state: Dict[str, Any]) -> NodeResult:
        payload = state["ingress_event"]

        if not isinstance(payload, dict):
            raise InvalidInputError("ingress_event must be a dict.")

        try:
            event = IngressEvent(**payload)
        except (TypeError, ValueError) as exc:
            raise InvalidInputError(f"Invalid ingress_event: {exc}") from exc

        normalized_text = event.text.strip()
        objective = self._derive_objective(normalized_text)

        patch = IngressStatePatch(
            input_text=normalized_text,
            objective=objective,
        )

        metrics = {
            "input_chars": len(normalized_text),
            "has_outcome": objective.outcome is not None,
            "event_type": event.event_type.value,
        }

        return NodeResult.success(
            state_patch=patch.to_dict(),
            metrics=metrics,
        )

    def _derive_objective(self, text: str) -> Objective:
        """
        Very naive objective extraction (v0 scaffold).

        Later this can be replaced by structured LLM/DSPy extraction.
        """
        text_lower = text.lower()

        if "analyze" in text_lower:
            action = "analyze"
        elif "create" in text_lower or "generate" in text_lower:
            action = "create"
        elif "optimize" in text_lower:
            action = "optimize"
        else:
            action = "understand"

        subject = text

        outcome = None
        if "to " in text_lower:
            try:
                outcome = text.split("to ", 1)[1].strip()
            except Exception:
                outcome = None

        return Objective(
            action=action,
            subject=subject,
            outcome=outcome,
        )