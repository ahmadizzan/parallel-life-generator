import asyncio
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

import typer
from rich import print
from sqlmodel import select, Session

from plg.export.markdown import render_tree_to_markdown
from plg.export.mermaid import render_tree_to_mermaid
from plg.models.db import get_session
from plg.models.models import BranchNode, ContextBlock, Decision
from plg.tools.analysis import annotate_branch
from plg.tools.branching import generate_branches
from plg.tools.context import collect_context, summarise_context
from plg.tools.show import generate_tree_view
from plg.tools.tree import expand_tree_bfs

app = typer.Typer()


class ExportFormat(str, Enum):
    markdown = "markdown"
    mermaid = "mermaid"


def _create_initial_decision(session: Session, context_data: dict) -> Decision:
    """Creates and saves the initial decision from collected context."""
    context_blocks = [
        ContextBlock(role=key, text=value) for key, value in context_data.items()
    ]
    new_decision = Decision(
        text="Initial context collected.", context_blocks=context_blocks
    )
    session.add(new_decision)
    session.commit()
    session.refresh(new_decision)
    return new_decision


async def _full_session_async(
    export_format: Optional[ExportFormat], max_depth: int, max_children: int
):
    """Orchestrates a full PLG session: collect -> expand -> export."""
    # Step 1: Collect Context
    print("\n[bold cyan]Step 1: Collect Initial Context[/bold cyan]")
    context_data = collect_context()

    start_decision_id = None
    with get_session() as session:
        new_decision = _create_initial_decision(session, context_data)
        print("\n[bold green]Context saved as new Decision![/bold green]")
        print(f"  Decision ID: {new_decision.id}")
        start_decision_id = new_decision.id

    # Step 2: Expand Tree
    print("\n\n[bold cyan]Step 2: Expanding Decision Tree...[/bold cyan]")
    await _expand_async(start_decision_id, max_depth, max_children)

    # Step 3: Export Tree (if requested)
    if export_format:
        print("\n\n[bold cyan]Step 3: Exporting Tree...[/bold cyan]")

        sessions_dir = Path.home() / "plg_sessions"
        sessions_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        extension = "md" if export_format == ExportFormat.markdown else "mmd"
        output_file = sessions_dir / f"session_{timestamp}.{extension}"

        await _export_async(start_decision_id, output_file, export_format)


@app.command()
def launch(
    max_depth: int = typer.Option(
        2, "--depth", "-d", help="The maximum depth of the expansion."
    ),
    max_children: int = typer.Option(
        2, "--children", "-c", help="The number of children to generate per node."
    ),
    export_format: Optional[ExportFormat] = typer.Option(
        None,
        "--export",
        "-e",
        case_sensitive=False,
        help="Export the generated tree to a timestamped file in ~/plg_sessions/.",
    ),
):
    """
    Launches a full Parallel Life Generator session from scratch.

    This command will first guide you through an interactive context collection.
    Then, it will automatically expand the decision tree based on your input.
    Finally, it can optionally export the full tree to a file.
    """
    asyncio.run(_full_session_async(export_format, max_depth, max_children))


@app.command()
def collect():
    """
    Runs the interactive context collection tool and saves the results
    as a new Decision in the database.
    """
    context_data = collect_context()

    with get_session() as session:
        new_decision = _create_initial_decision(session, context_data)
        print("\n[bold green]Context saved as new Decision![/bold green]")
        print(f"  Decision ID: {new_decision.id}")
        print(f"  Timestamp: {new_decision.created_at.isoformat()}")


async def _summarise_async(decision_id: int):
    """Async logic for the summarise command."""
    print(f"Summarizing context for Decision ID: {decision_id}...")
    with get_session() as session:
        decision = session.get(Decision, decision_id)
        if not decision:
            print(f"[bold red]Error:[/bold red] Decision ID {decision_id} not found.")
            raise typer.Exit(code=1)

        if not decision.context_blocks:
            print("No context blocks found for this decision.")
            # Return the decision text itself if no context to summarize
            return decision.text

        summary = await summarise_context(decision.context_blocks)
        print("\n[bold green]Generated Summary:[/bold green]")
        print(summary)
        return summary


@app.command()
def summarise(
    decision_id: int = typer.Argument(..., help="The ID of the decision to summarise."),
):
    """
    Summarises the context associated with a given Decision ID.
    """
    asyncio.run(_summarise_async(decision_id))


async def _branch_async(decision_id: int, max_children: int):
    """Async logic for the branch command."""
    summary = await _summarise_async(decision_id)
    if not summary:
        print(
            "[bold red]Error:[/bold red] Could not generate a summary to branch from."
        )
        raise typer.Exit(code=1)

    with get_session() as session:
        parent_decision = session.get(Decision, decision_id)
        if not parent_decision:
            # This check is redundant if _summarise_async already did it,
            # but it's good practice to be safe.
            print(f"[bold red]Error:[/bold red] Decision ID {decision_id} not found.")
            raise typer.Exit(code=1)

        print(f"\nGenerating {max_children} branches for Decision ID: {decision_id}...")
        branches = await generate_branches(
            parent_summary=summary,
            context_blocks=parent_decision.context_blocks,
            depth=0,  # Assuming this is the first level of branching
            max_children=max_children,
        )

        if not branches:
            print(
                "[bold yellow]Warning:[/bold yellow] The LLM did not return any branches."
            )
            return

        # Find or create the parent BranchNode
        parent_node = session.exec(
            select(BranchNode).where(BranchNode.decision_id == decision_id)
        ).first()

        if not parent_node:
            parent_node = BranchNode(decision=parent_decision)
            session.add(parent_node)

        # Create new Decisions and BranchNodes for each generated branch
        new_decisions = []
        for branch_text in branches:
            child_decision = Decision(text=branch_text)
            child_node = BranchNode(decision=child_decision, parent=parent_node)
            session.add(child_decision)
            session.add(child_node)
            new_decisions.append(child_decision)

        session.commit()

        print(
            f"\n[bold green]Saved {len(new_decisions)} new branches to the database.[/bold green]"
        )
        for decision in new_decisions:
            session.refresh(decision)
            print(f"  - Created Decision ID: {decision.id}")


@app.command()
def branch(
    decision_id: int = typer.Argument(..., help="The ID of the parent decision."),
    max_children: int = typer.Option(
        3, "--max-children", "-c", help="The maximum number of branches to generate."
    ),
):
    """
    Generates new parallel branches from a given Decision ID and saves them
    as new Decisions and BranchNodes in the database.
    """
    asyncio.run(_branch_async(decision_id, max_children))


async def _annotate_async(decision_id: int):
    """Async logic for the annotate command."""
    print(f"Analyzing decision text for Decision ID: {decision_id}...")
    with get_session() as session:
        decision = session.get(Decision, decision_id)
        if not decision:
            print(f"[bold red]Error:[/bold red] Decision ID {decision_id} not found.")
            raise typer.Exit(code=1)

        annotations = await annotate_branch(decision.text)

        if not annotations:
            print(
                "[bold yellow]Warning:[/bold yellow] The LLM did not return any annotations."
            )
            return

        print("\n[bold green]Generated Annotations:[/bold green]")
        print(annotations)
        return annotations


@app.command()
def annotate(
    decision_id: int = typer.Argument(..., help="The ID of the decision to annotate."),
):
    """
    Analyzes a given Decision's text to extract strategic tags.
    """
    asyncio.run(_annotate_async(decision_id))


async def _expand_async(decision_id: int, max_depth: int, max_children: int):
    """Async logic for the expand command."""
    await expand_tree_bfs(
        start_decision_id=decision_id,
        max_depth=max_depth,
        max_children=max_children,
    )


@app.command()
def expand(
    decision_id: int = typer.Argument(
        ..., help="The ID of the decision to start the expansion from."
    ),
    max_depth: int = typer.Option(
        2, "--depth", "-d", help="The maximum depth of the expansion."
    ),
    max_children: int = typer.Option(
        2, "--children", "-c", help="The number of children to generate per node."
    ),
):
    """
    Automatically expands the decision tree from a starting decision.
    """
    asyncio.run(_expand_async(decision_id, max_depth, max_children))


async def _export_async(decision_id: int, output_file: Path, format: ExportFormat):
    """Async logic for the export command."""
    with get_session() as session:
        # Find the root node for the export
        root_node = session.exec(
            select(BranchNode).where(BranchNode.decision_id == decision_id)
        ).first()

        if not root_node:
            print(
                f"[bold red]Error:[/bold red] No branch data found for Decision ID {decision_id}. Try running 'plg branch' or 'plg expand' first."
            )
            raise typer.Exit(code=1)

        print(
            f"Exporting tree starting from Decision ID {decision_id} in {format.value} format..."
        )

        content = ""
        if format == ExportFormat.markdown:
            content = await render_tree_to_markdown(root_node.id, session)
        elif format == ExportFormat.mermaid:
            content = await render_tree_to_mermaid(root_node.id, session)

        output_file.write_text(content)
        print(f"\n[bold green]Successfully exported tree to {output_file}[/bold green]")


@app.command()
def export(
    decision_id: int = typer.Argument(
        ..., help="The ID of the root decision of the tree to export."
    ),
    output_file: Path = typer.Argument(
        ..., help="The path to the output markdown file.", writable=True
    ),
    format: ExportFormat = typer.Option(
        ExportFormat.markdown,
        "--format",
        "-f",
        help="The output format for the exported tree.",
    ),
):
    """
    Exports a decision tree to a markdown file.
    """
    asyncio.run(_export_async(decision_id, output_file, format))


async def _show_async(decision_id: int):
    """Async logic for the show command."""
    with get_session() as session:
        # Find the root node for the tree
        root_node = session.exec(
            select(BranchNode).where(BranchNode.decision_id == decision_id)
        ).first()

        if not root_node:
            print(
                f"[bold red]Error:[/bold red] No branch data found for Decision ID {decision_id}. Try running 'plg branch' or 'plg expand' first."
            )
            raise typer.Exit(code=1)

        print(f"Generating tree view for Decision ID {decision_id}...")
        rich_tree = await generate_tree_view(root_node.id, session)
        print(rich_tree)


@app.command()
def show(
    decision_id: int = typer.Argument(
        ..., help="The ID of the root decision of the tree to show."
    ),
):
    """
    Shows a decision tree in the CLI.
    """
    asyncio.run(_show_async(decision_id))


if __name__ == "__main__":
    app()
