import asyncio
from pprint import pprint
import sys
from pathlib import Path

# Add project root to Python path
workspace_root = Path(__file__).parent.parent
if str(workspace_root) not in sys.path:
    sys.path.insert(0, str(workspace_root))

from nodes.ingress.node import IngressNode


async def main() -> None:
    node = IngressNode()

    print("=== SUCCESS CASE ===")
    good_state = {
        "ingress_event": {
            "event_type": "user_text",
            "text": "Analyze new product launch messaging to recommend next actions",
            "source": "ui",
        }
    }

    good_result = await node.run(good_state)
    pprint(good_result)

    print("\n=== FAILURE CASE: missing ingress_event ===")
    missing_state = {}
    missing_result = await node.run(missing_state)
    pprint(missing_result)

    print("\n=== FAILURE CASE: empty text ===")
    empty_text_state = {
        "ingress_event": {
            "event_type": "user_text",
            "text": "   ",
            "source": "ui",
        }
    }

    empty_result = await node.run(empty_text_state)
    pprint(empty_result)

    print("\n=== FAILURE CASE: wrong type for ingress_event ===")
    bad_type_state = {
        "ingress_event": "not a dict",
    }
    bad_type_result = await node.run(bad_type_state)
    pprint(bad_type_result)


if __name__ == "__main__":
    asyncio.run(main())