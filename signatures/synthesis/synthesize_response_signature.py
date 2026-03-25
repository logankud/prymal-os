"""
SynthesizeResponseSignature — the synthesis layer's DSPy contract.

Takes the original user request and all completed TaskResults, and
produces a structured SynthesisResult. This is the final node in the
pipeline — its output is what the user receives.

Design principles:
- Use structured Pydantic types natively (no JSON serialization)
- Enforce grounding: only state what artifacts support
- Require explicit confidence scoring
- Surface gaps and open questions rather than hallucinating
"""

from __future__ import annotations

from typing import List

import dspy

from signatures.synthesis.types import SynthesisResult, TaskResult


class SynthesizeResponseSignature(dspy.Signature):
    """
    You are a senior synthesis analyst. Your job is to take the user's original
    request and the completed work from one or more workers, and produce a
    structured, accurate response.

    Strict rules:
    1. GROUNDING: Only state findings that are supported by the provided task results.
       Do not invent, extrapolate, or fill in gaps with plausible-sounding content.
    2. CONFIDENCE: Set confidence low (< 0.5) if:
       - Workers reported significant gaps
       - Task results are insufficient to answer the user's request
       - The findings are speculative or unverified
    3. GAPS: Surface every gap from the task results in open_questions.
       A false positive (hallucinated confident answer) is worse than
       a transparent low-confidence response.
    4. SPECIFICITY: Be specific about what was found. Generic summaries
       that could apply to any request are not acceptable.
    5. AUDIENCE: Write for the person who made the original request —
       they want to know what was found and what to do next, not how
       the system works internally.
    """

    user_request: str = dspy.InputField(
        desc="The original user request, verbatim."
    )
    task_results: List[TaskResult] = dspy.InputField(
        desc=(
            "Completed TaskResult objects from all workers. "
            "Each contains the task objective, the worker's primary finding, "
            "full detail, confidence, and any gaps the worker identified."
        )
    )

    synthesis: SynthesisResult = dspy.OutputField(
        desc=(
            "A structured synthesis of all task results into a single coherent response. "
            "Must be grounded in the task_results — no additional facts may be introduced."
        )
    )
