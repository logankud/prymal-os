# kernel/artifacts/__init__.py

from artifacts.base import (
    ArtifactKind,
    BaseArtifact,
    BasePayload,
)
from artifacts.analysis import (
    AnalysisArtifact,
    AnalysisPayload,
    EvidenceItem,
    Hypothesis,
    SuggestedTask,
)
from artifacts.recommendation import (
    RecommendationArtifact,
    RecommendationItem,
    RecommendationPayload,
)
from artifacts.content import (
    ContentArtifact,
    ContentPayload,
)
from artifacts.report import (
    ReportArtifact,
    ReportPayload,
    ReportSection,
)
from artifacts.action import (
    ActionArtifact,
    ActionPayload,
)
from artifacts.signal import (
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
