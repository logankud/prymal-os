"""
Ingress refine pass — precision-optimized structuring of a single work intent.

This signature takes one plain-language intent candidate (produced by
ExtractIntentSignature) and maps it into a fully typed ParsedIntent.
The goal is high precision: only extract what is clearly present,
never infer beyond what the candidate and original input support.
"""

import dspy

from signatures.ingress.types import ParsedIntent


class RefineIntentSignature(dspy.Signature):
    """
    Refine a single plain-language work intent into a structured ParsedIntent.

    Given one intent candidate and the original input for context, extract
    the action verb, subject, optional outcome, and business domain with
    high confidence. Do not infer fields that are not clearly supported by
    the text. If the outcome is ambiguous, leave it as None.
    """

    intent_candidate: str = dspy.InputField(
        desc=(
            "A plain-language description of a single work intent, "
            "as produced by the extract pass."
        )
    )
    input_text: str = dspy.InputField(
        desc="The original user input, provided for context and disambiguation."
    )

    intent: ParsedIntent = dspy.OutputField(
        desc=(
            "A fully structured work intent with action, subject, optional outcome, "
            "and domain classification."
        )
    )
