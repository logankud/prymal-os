from kernel.tasks.task import TaskDomain
from kernel.workers.spec import WorkerSpec


COO_WORKER = WorkerSpec(
    worker_id="coo_worker",
    supported_domains=(TaskDomain.OPERATIONS,),
    display_name="COO Worker",
    description="Handles operations-oriented tasks.",
    tags=("operations", "ops"),
)

CMO_WORKER = WorkerSpec(
    worker_id="cmo_worker",
    supported_domains=(TaskDomain.MARKETING,),
    display_name="CMO Worker",
    description="Handles marketing-oriented tasks.",
    tags=("marketing", "growth"),
)

RESEARCH_WORKER = WorkerSpec(
    worker_id="research_worker",
    supported_domains=(TaskDomain.RESEARCH,),
    display_name="Research Worker",
    description="Handles research-oriented tasks.",
    tags=("research",),
)

GENERAL_WORKER = WorkerSpec(
    worker_id="general_worker",
    supported_domains=(TaskDomain.GENERAL,),
    display_name="General Worker",
    description="Handles general-purpose tasks.",
    tags=("general",),
)

WORKER_SPECS = (
    COO_WORKER,
    CMO_WORKER,
    RESEARCH_WORKER,
    GENERAL_WORKER,
)