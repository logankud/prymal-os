from __future__ import annotations

import asyncio
from typing import Any, Dict, List

import dspy

from config.core import ModelClass
from kernel.model import get_lm
from kernel.nodes.base import BaseNode
from kernel.nodes.errors import InvalidInputError, MissingRequiredStateError
from kernel.nodes.result import NodeObservation, NodeResult, ObservationCategory
from nodes.ingress.schema import IngressEvent, IngressStatePatch
from signatures.ingress import ExtractIntentSignature, ParsedIntent, RefineIntentSignature


class IngressNode(BaseNode):
    """
    Ingress Node (v1)

    Responsibilities:
    - Validate and parse the incoming ingress_event
    - Normalize input text
    - Extract all candidate intents (recall pass via ExtractIntentSignature)
    - Refine each candidate into a structured ParsedIntent (precision pass via RefineIntentSignature)
    - Return a typed IngressStatePatch with the full list of parsed intents

    Out of scope:
    - Task creation
    - Routing
    - Planning
    - Execution
    """

    name = "ingress_node"

    def __init__(self) -> None:
        self._lm = get_lm(ModelClass.CHEAP)
        self._extract = dspy.ChainOfThought(ExtractIntentSignature)
        self._refine = dspy.ChainOfThought(RefineIntentSignature)

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

        # --- Pass 1: Extract (recall) ---
        # Cast a wide net — surface every possible unit of work.
        with dspy.context(lm=self._lm):
            extract_result = await asyncio.to_thread(
                self._extract,
                input_text=normalized_text,
                event_type=event.event_type.value,
            )
        candidates: List[str] = extract_result.intent_candidates

        # --- Pass 2: Refine (precision) ---
        # Structure each candidate independently. Failures are isolated
        # so one bad candidate doesn't discard the rest.
        intents: List[ParsedIntent] = []
        refine_errors: List[str] = []

        for candidate in candidates:
            try:
                with dspy.context(lm=self._lm):
                    refine_result = await asyncio.to_thread(
                        self._refine,
                        intent_candidate=candidate,
                        input_text=normalized_text,
                    )
                intent = refine_result.intent
                if isinstance(intent, dict):
                    intent = ParsedIntent(**intent)
                intents.append(intent)
            except Exception as exc:
                refine_errors.append(f"Failed to refine candidate '{candidate}': {exc}")

        patch = IngressStatePatch(
            input_text=normalized_text,
            event_type=event.event_type.value,
            intents=intents,
        )

        observations = [
            NodeObservation(
                name="extract_pass",
                value={"candidates": candidates},
                category=ObservationCategory.INGESTION,
                message=f"Extracted {len(candidates)} candidate intent(s)",
                tags=["ingress", "extract"],
            ),
            *[
                NodeObservation(
                    name="intent_refined",
                    value={
                        "action": intent.action,
                        "subject": intent.subject,
                        "domain": intent.domain,
                    },
                    category=ObservationCategory.CLASSIFICATION,
                    message=f"{intent.action} · {intent.subject} → {intent.domain}",
                    tags=["ingress", "refine", intent.domain],
                )
                for intent in intents
            ],
        ]

        metrics = {
            "input_chars": len(normalized_text),
            "event_type": event.event_type.value,
            "candidates_found": len(candidates),
            "intents_refined": len(intents),
            "refine_errors": len(refine_errors),
        }

        if refine_errors:
            return NodeResult.partial_success(
                state_patch=patch.to_dict(),
                observations=observations,
                metrics=metrics,
                errors=refine_errors,
            )

        return NodeResult.success(
            state_patch=patch.to_dict(),
            observations=observations,
            metrics=metrics,
        )
