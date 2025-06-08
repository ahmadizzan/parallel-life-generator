from rich.tree import Tree
from sqlmodel import Session

from plg.models.models import BranchNode
from plg.tools.analysis import annotate_branch
from plg.tools.context import summarise_context


async def _build_rich_tree_level(
    node: BranchNode, tree: Tree, session: Session, is_root: bool = False
):
    """
    Recursively builds a `rich.tree.Tree` by fetching data for a node
    and all its children.

    Args:
        node: The current BranchNode to add to the tree.
        tree: The rich.tree.Tree object to add the new node to.
        session: The active database session.
        is_root: Flag to indicate if the current node is the root.
    """
    if not node.decision:
        return

    # 1. Fetch annotations and summary for the current node.
    decision_text = node.decision.text

    summary_text = ""
    if is_root and node.decision.context_blocks:
        summary = await summarise_context(node.decision.context_blocks)
        summary_text = f"\n[dim]Summary:[/dim] [italic]{summary}[/italic]"

    annotations = await annotate_branch(decision_text)
    risk = annotations.get("risk", "N/A")
    growth = annotations.get("growth", "N/A")
    emotion = annotations.get("emotion", "N/A")

    # 2. Format the node's display text.
    node_label = (
        f"[bold]Decision (ID: {node.decision.id})[/bold]: {decision_text}"
        f"{summary_text}\n"
        f"[italic]Tags: [Risk: {risk}] [Growth: {growth}] [Emotion: {emotion}][/italic]"
    )

    # 3. Add the node to the rich tree.
    branch = tree.add(node_label)

    # 4. Recursively call for children.
    # We use a direct query here to ensure children are loaded within the session.
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
