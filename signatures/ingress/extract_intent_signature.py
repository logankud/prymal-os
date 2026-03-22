"""
Ingress extract pass — recall-optimized enumeration of work intents.

This signature casts a wide net: it should surface every possible unit of
work in the input without worrying about structure or certainty. The goal
is high recall. Precision is handled downstream by RefineIntentSignature.
"""

import dspy


class ExtractIntentSignature(dspy.Signature):
    """
    Extract every distinct work intent from the input, erring on the side of inclusion.

    A work intent is any discrete unit of work: a request, a task, an action
    someone wants taken, or an outcome they want achieved. If something could
    be a work intent, include it. Do not merge separate intents into one entry,
    and do not impose structure on the descriptions — plain language only.

    Works for typed text and voice transcript inputs.
    """

    input_text: str = dspy.InputField(
        desc="Raw user input expressing one or more work intents, ideas, or requests."
    )
    event_type: str = dspy.InputField(
        desc=(
            "Source of the input: user_text, voice_transcript, "
            "api_event, or system_event. Use this to adjust interpretation "
            "(e.g. voice transcripts may contain filler words or run-on sentences)."
        )
    )

    intent_candidates: list[str] = dspy.OutputField(
        desc=(
            "An exhaustive list of distinct work intents found in the input. "
            "Each entry is a concise plain-language description of one unit of work. "
            "Preserve the user's original phrasing where possible. "
            "Return at least one entry even for simple single-intent inputs."
        )
    )
