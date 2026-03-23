from __future__ import annotations

from kernel.tasks.task import TaskDomain
from kernel.workers.spec import WorkerSpec
from workers.general_worker import GeneralWorker
from workers.marketing_worker import MarketingWorker
from workers.operations_worker import OperationsWorker
from workers.research_worker import ResearchWorker


GENERAL_WORKER = WorkerSpec(
    worker_id="general_worker",
    supported_domains=(TaskDomain.GENERAL,),
    display_name="General Worker",
    description="Handles general-purpose tasks.",
    tags=("general",),
    implementation_cls=GeneralWorker,
)

CMO_WORKER = WorkerSpec(
    worker_id="cmo_worker",
    supported_domains=(TaskDomain.MARKETING,),
    display_name="CMO Worker",
    description="Handles marketing-oriented tasks.",
    tags=("marketing", "growth"),
    implementation_cls=MarketingWorker,
)

COO_WORKER = WorkerSpec(
    worker_id="coo_worker",
    supported_domains=(TaskDomain.OPERATIONS,),
    display_name="COO Worker",
    description="Handles operations-oriented tasks.",
    tags=("operations", "ops"),
    implementation_cls=OperationsWorker,
)

RESEARCH_WORKER = WorkerSpec(
    worker_id="research_worker",
    supported_domains=(TaskDomain.RESEARCH,),
    display_name="Research Worker",
    description="Handles research-oriented tasks.",
    tags=("research",),
    implementation_cls=ResearchWorker,
)

WORKER_SPECS = (
    COO_WORKER,
    CMO_WORKER,
    RESEARCH_WORKER,
    GENERAL_WORKER,
)