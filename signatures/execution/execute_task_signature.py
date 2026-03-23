"""
Worker execution signature — drives all domain workers.

Takes a structured task objective and produces a complete work deliverable.
Each worker binds this signature with domain-specific instructions via
the docstring override pattern.
"""

import dspy


class ExecuteTaskSignature(dspy.Signature):
    """
    Execute a work task and produce a high-quality deliverable.

    You are a skilled professional executing real work. Based on the task
    objective, produce a specific, actionable, and well-reasoned output
    appropriate to the domain and action type.

    For analysis tasks: examine the subject, surface key findings, and
    identify what is known, uncertain, and recommended.

    For drafting/content tasks: produce the actual content — not a description
    of what the content should say, but the content itself.

    For planning tasks: produce a concrete plan with steps, owners, and rationale.

    Be specific. Generic outputs are not acceptable.
    """

    action: str = dspy.InputField(
        desc="The primary action verb describing the work (e.g. analyze, draft, plan, research, summarize)"
    )
    subject: str = dspy.InputField(
        desc="The specific entity, topic, or asset the action is applied to"
    )
    outcome: str = dspy.InputField(
        desc="The desired result or goal of the work"
    )
    domain: str = dspy.InputField(
        desc="Business domain context: operations, marketing, research, or general"
    )

    executive_summary: str = dspy.OutputField(
        desc=(
            "2-3 sentence summary of the key output. "
            "Should be readable standalone without the full deliverable."
        )
    )
    deliverable: str = dspy.OutputField(
        desc=(
            "The complete work product. This is the actual output of the task — "
            "detailed analysis, drafted content, research findings, or action plan. "
            "Must be thorough, specific, and directly address the task objective."
        )
    )
