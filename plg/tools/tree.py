from typing import List

from sqlmodel import select, Session

from plg.models.db import get_session
from plg.models.models import BranchNode, Decision
from plg.tools.branching import generate_branches
from plg.tools.context import summarise_context


def _get_start_node(session: Session, start_decision_id: int) -> BranchNode:
    """Finds or creates the starting BranchNode for the expansion."""
    node = session.exec(
        select(BranchNode).where(BranchNode.decision_id == start_decision_id)
    ).first()
    if node:
        return node

    decision = session.get(Decision, start_decision_id)
    if not decision:
        raise ValueError(f"Decision ID {start_decision_id} not found.")

    new_node = BranchNode(decision=decision)
    session.add(new_node)
    session.commit()
    session.refresh(new_node)
    return new_node


async def expand_tree_bfs(start_decision_id: int, max_depth: int, max_children: int):
    """
    Expands a decision tree using a Breadth-First Search (BFS) approach.

    Args:
        start_decision_id: The ID of the Decision to start the expansion from.
        max_depth: The maximum depth to expand the tree to.
        max_children: The number of child branches to generate for each node.
    """
    with get_session() as session:
        try:
            start_node = _get_start_node(session, start_decision_id)
            print(
                f"Starting tree expansion from Decision ID {start_decision_id} (BranchNode ID {start_node.id})..."
            )
        except ValueError as e:
            print(f"[bold red]Error:[/bold red] {e}")
            return

        queue: List[BranchNode] = [start_node]

        for depth in range(max_depth):
            level_size = len(queue)
            print(f"Expanding level {depth + 1} with {level_size} nodes...")
            if level_size == 0:
                print("No more nodes to expand.")
                break

            next_level_nodes = []
            for _ in range(level_size):
                parent_node = queue.pop(0)
                parent_decision = parent_node.decision

                if not parent_decision:
                    continue

                if not parent_decision.context_blocks:
                    summary = parent_decision.text
                else:
                    summary = await summarise_context(parent_decision.context_blocks)

                branches = await generate_branches(
                    parent_summary=summary,
                    context_blocks=parent_decision.context_blocks,
                    depth=depth,
                    max_children=max_children,
                )

                for branch_text in branches:
                    child_decision = Decision(text=branch_text)
                    child_node = BranchNode(decision=child_decision, parent=parent_node)
                    session.add(child_decision)
                    session.add(child_node)
                    next_level_nodes.append(child_node)

            session.commit()
            for node in next_level_nodes:
                session.refresh(node)

            queue.extend(next_level_nodes)

    print("Tree expansion complete.")
