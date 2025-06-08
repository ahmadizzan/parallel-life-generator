import json
from typing import List

from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from sqlmodel import select, Session

from plg.models.db import get_session
from plg.models.models import BranchNode, Decision
from plg.tools.analysis import annotate_branch
from plg.tools.branching import generate_branches
from plg.tools.exceptions import MaxNodesExceededError


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

    Raises:
        MaxNodesExceededError: If the number of nodes exceeds 50.
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
        node_count = 1
        max_nodes = 50

        # Get the context from the root node, to be passed down.
        root_decision = session.get(Decision, start_decision_id)
        if not root_decision:
            print("[bold red]Error:[/bold red] Root decision not found.")
            return
        root_context_blocks = root_decision.context_blocks

        for depth in range(max_depth):
            level_size = len(queue)
            print(f"Expanding level {depth + 1} with {level_size} nodes...")
            if level_size == 0:
                print("No more nodes to expand.")
                break

            next_level_nodes = []
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("{task.completed}/{task.total}"),
                transient=True,
            ) as progress:
                task = progress.add_task(
                    f"Generating children for level {depth + 1}", total=level_size
                )
                for _ in range(level_size):
                    parent_node = queue.pop(0)
                    progress.update(task, advance=1)
                    parent_decision = parent_node.decision

                    if not parent_decision:
                        continue

                    if node_count >= max_nodes:
                        session.commit()
                        raise MaxNodesExceededError()

                    summary = parent_decision.summary or parent_decision.text

                    branches = await generate_branches(
                        parent_summary=summary,
                        context_blocks=root_context_blocks,
                        max_children=max_children,
                    )

                    for branch in branches:
                        if node_count >= max_nodes:
                            session.commit()  # Save progress before stopping
                            raise MaxNodesExceededError()

                        branch_text = branch["decision"]
                        tradeoffs = branch["tradeoffs"]
                        annotations = await annotate_branch(branch_text)

                        child_decision = Decision(
                            text=branch_text,
                            tradeoffs=json.dumps(tradeoffs),
                            tags=json.dumps(annotations),
                        )
                        child_node = BranchNode(
                            decision=child_decision, parent=parent_node
                        )
                        session.add(child_decision)
                        session.add(child_node)
                        next_level_nodes.append(child_node)
                        node_count += 1

            session.commit()
            for node in next_level_nodes:
                session.refresh(node)

            queue.extend(next_level_nodes)

    print("Tree expansion complete.")
