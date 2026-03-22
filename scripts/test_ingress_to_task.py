import asyncio
import sys
from pathlib import Path
from pprint import pprint

# Add project root to Python path
workspace_root = Path(__file__).parent.parent
if str(workspace_root) not in sys.path:
    sys.path.insert(0, str(workspace_root))

from nodes.ingress.node import IngressNode
from kernel.tasks.materialize import task_from_ingress_result


async def main() -> None:
    node = IngressNode()

    print("=== INGRES S-> TASK SUCCESS CASE ===")
    state = {
        "ingress_event": {
            "event_type": "user_text",
            "text": "Analyze new product launch messaging to recommend next actions",
            "source": "ui",
        }
    }

    result = await node.run(state)
    print("\n[NodeResult]")
    pprint(result)

    if not result.ok:
        print("\nIngress failed unexpectedly.")
        return

    task = task_from_ingress_result(result)

    print("\n[Materialized Task]")
    pprint(task)

    print("\n[Task as dict]")
    pprint(task.to_dict())

    print("\n=== INGRESS -> TASK FAILURE CASE ===")
    bad_state = {
        "ingress_event": {
            "event_type": "user_text",
            "text": "   ",
            "source": "ui",
        }
    }

    bad_result = await node.run(bad_state)
    print("\n[Bad NodeResult]")
    pprint(bad_result)

    if bad_result.ok:
        print("\nUnexpected success; expected ingress failure.")
        return

    print("\nSkipping task materialization because ingress did not succeed.")


if __name__ == "__main__":
    asyncio.run(main())