# kernel/artifacts/__init__.py

from kernel.artifacts.base import (
    ArtifactKind,
    BaseArtifact,
    BasePayload,
)
from kernel.artifacts.analysis import (
    AnalysisArtifact,
    AnalysisPayload,
    EvidenceItem,
    Hypothesis,
    SuggestedTask,
)
from kernel.artifacts.recommendation import (
    RecommendationArtifact,
    RecommendationItem,
    RecommendationPayload,
)
from kernel.artifacts.content import (
    ContentArtifact,
    ContentPayload,
)
from kernel.artifacts.report import (
    ReportArtifact,
    ReportPayload,
    ReportSection,
)
from kernel.artifacts.action import (
    ActionArtifact,
    ActionPayload,
)
from kernel.artifacts.signal import (
    SignalArtifact,
    SignalPayload,
)

__all__ = [
    # base
    "ArtifactKind",
    "BaseArtifact",
    "BasePayload",
    # analysis
    "AnalysisArtifact",
    "AnalysisPayload",
    "EvidenceItem",
    "Hypothesis",
    "SuggestedTask",
    # recommendation
    "RecommendationArtifact",
    "RecommendationItem",
    "RecommendationPayload",
    # content
    "ContentArtifact",
    "ContentPayload",
    # report
    "ReportArtifact",
    "ReportPayload",
    "ReportSection",
    # action
    "ActionArtifact",
    "ActionPayload",
    # signal
    "SignalArtifact",
    "SignalPayload",
]
