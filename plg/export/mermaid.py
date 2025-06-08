from sqlmodel import Session

from plg.models.models import BranchNode
from plg.tools.analysis import annotate_branch


async def render_tree_to_mermaid(start_node_id: int, session: Session) -> str:
    """
    Renders a decision tree starting from a given node into a Mermaid graph string.

    This function uses a Breadth-First Search (BFS) to traverse the tree
    and build the graph definition.

    Args:
        start_node_id: The ID of the BranchNode to start the export from.
        session: The active database session.

    Returns:
        A string containing the full Mermaid graph definition.
    """
    start_node = session.get(BranchNode, start_node_id)
    if not start_node:
        return "Error: Start node not found."

    graph_lines = set()
    queue = [start_node]
    visited_nodes = set()

    while queue:
        node = queue.pop(0)
        if node.id in visited_nodes or not node.decision:
            continue
        visited_nodes.add(node.id)

        # Sanitize decision text for Mermaid label
        # Quotes must be replaced with the #quot; HTML entity.
        decision_text = node.decision.text.replace('"', "#quot;")
        annotations = await annotate_branch(decision_text)
        risk = annotations.get("risk", "N/A")
        growth = annotations.get("growth", "N/A")
        emotion = annotations.get("emotion", "N/A")

        node_id = f"D{node.decision_id}"
        node_label = (
            f'"{decision_text}<br/>'
            f'[Risk: {risk}] [Growth: {growth}] [Emotion: {emotion}]"'
        )
        graph_lines.add(f"    {node_id}[{node_label}]")

        for child_node in node.children:
            child_id = f"D{child_node.decision_id}"
            graph_lines.add(f"    {node_id} --> {child_id}")
            queue.append(child_node)

    # Sort lines for deterministic output, making it easier to test/compare
    sorted_lines = "\n".join(sorted(list(graph_lines)))
    return f"graph TD\n{sorted_lines}\n"
