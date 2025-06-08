import json
from rich.tree import Tree
from sqlmodel import Session

from plg.models.models import BranchNode


def _get_compact_tradeoffs(tradeoffs: list) -> list:
    """Selects and formats a compact list of tradeoffs."""
    pros = [t for t in tradeoffs if t.startswith("+")]
    cons = [t for t in tradeoffs if t.startswith("-")]

    compact_list = []
    if pros:
        compact_list.append(pros[0])
    if cons:
        compact_list.append(cons[0])
    if len(compact_list) < 2 and len(pros) > 1:
        compact_list.append(pros[1])

    return [t.replace("+", "✔").replace("-", "✘") for t in compact_list]


async def _build_rich_tree_level(
    node: BranchNode, tree: Tree, session: Session, is_root: bool = False
):
    """
    Recursively builds a `rich.tree.Tree` by fetching data for a node
    and all its children.
    """
    if not node.decision:
        return

    decision = node.decision
    node_label = ""

    if is_root:
        title = f"📍 Root Context (ID: {decision.id})"
        summary = decision.summary or "No summary available."
        node_label = f"[bold]{title}[/bold]\n\n[italic]{summary}[/italic]"
    else:
        # 1. Title
        title = decision.text
        title_line = f"📍 Decision (ID: {decision.id}): {title}"

        # 2. Tags
        tags_line = ""
        if decision.tags:
            try:
                tags = json.loads(decision.tags)
                risk = tags.get("risk", "N/A")
                growth = tags.get("growth", "N/A")
                emotion = tags.get("emotion", "N/A")
                tags_line = (
                    f"Tags: [Risk: {risk}] [Growth: {growth}] [Emotion: {emotion}]"
                )
            except (json.JSONDecodeError, TypeError):
                tags_line = "Tags: Error parsing tags"

        # 3. Summary (first sentence)
        summary_line = ""
        if decision.summary:
            summary = decision.summary.split(".")[0] + "."
            summary_line = f"Summary: {summary}"

        # 4. Tradeoffs (compact view)
        tradeoffs_lines = []
        if decision.tradeoffs:
            try:
                tradeoffs = json.loads(decision.tradeoffs)
                if tradeoffs:
                    compact_tradeoffs = _get_compact_tradeoffs(tradeoffs)
                    tradeoffs_lines.append("Tradeoffs:")
                    for t in compact_tradeoffs:
                        tradeoffs_lines.append(f"  {t}")
            except (json.JSONDecodeError, TypeError):
                tradeoffs_lines.append("Tradeoffs: Error parsing")

        # 5. Assemble the node content
        content = [title_line, tags_line, summary_line]
        if tradeoffs_lines:
            content.extend(tradeoffs_lines)

        node_label = "\n".join(line for line in content if line)

    branch = tree.add(node_label)

    # Recursively call for children.
    for child_node in node.children:
        await _build_rich_tree_level(child_node, branch, session)


async def generate_tree_view(start_node_id: int, session: Session) -> Tree:
    """
    Generates a `rich.tree.Tree` for display in the console.

    Args:
        start_node_id: The ID of the BranchNode to start the tree from.
        session: The active database session.

    Returns:
        A `rich.tree.Tree` object ready to be printed.
    """
    start_node = session.get(BranchNode, start_node_id)
    if not start_node or not start_node.decision:
        return Tree("[bold red]Error: Start node not found.[/bold red]")

    tree = Tree(
        f"🌳 [bold green]Decision Tree starting from Decision ID: {start_node.decision.id}[/bold green]"
    )
    await _build_rich_tree_level(start_node, tree, session, is_root=True)
    return tree
