from sqlmodel import Session

from plg.models.models import BranchNode
from plg.tools.analysis import annotate_branch


async def _build_markdown_level(node: BranchNode, level: int) -> str:
    """
    Recursively builds a markdown string for a single node and its children.
    This function assumes the node is attached to an active database session.
    """
    if not node.decision:
        return ""

    # 1. Get the decision text and annotations for the current node.
    decision_text = node.decision.text
    annotations = await annotate_branch(decision_text)
    risk = annotations.get("risk", "N/A")
    growth = annotations.get("growth", "N/A")
    emotion = annotations.get("emotion", "N/A")

    # 2. Format the current node's markdown entry.
    indent = "  " * level
    md_parts = [
        f"{indent}- **Decision (ID: {node.decision_id})**: {decision_text}",
        f"{indent}  - *Tags: [Risk: {risk}] [Growth: {growth}] [Emotion: {emotion}]*",
    ]

    # 3. Recursively call for children. The lazy-load of `node.children` will
    #    work because the session remains open during the entire process.
    for child_node in node.children:
        md_parts.append(await _build_markdown_level(child_node, level + 1))

    return "\n".join(md_parts)


async def render_tree_to_markdown(start_node_id: int, session: Session) -> str:
    """
    Renders a decision tree starting from a given node into a markdown string.

    Args:
        start_node_id: The ID of the BranchNode to start the export from.
        session: The active database session.

    Returns:
        A string containing the full markdown representation of the tree.
    """
    start_node = session.get(BranchNode, start_node_id)
    if not start_node:
        return "Error: Start node not found."

    header = f"# Decision Tree Export\n\nStarting from Decision ID: {start_node.decision_id}\n\n"
    tree_md = await _build_markdown_level(start_node, 0)
    return header + tree_md
