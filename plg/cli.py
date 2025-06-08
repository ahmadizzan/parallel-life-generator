import asyncio
import typer
from rich import print
from sqlmodel import select

from plg.llm.factory import get_llm_client
from plg.models.db import get_session
from plg.models.models import BranchNode, ContextBlock, Decision
from plg.tools.analysis import annotate_branch
from plg.tools.branching import generate_branches
from plg.tools.context import collect_context, summarise_context
from plg.tools.tree import expand_tree_bfs


app = typer.Typer()


async def _launch_async():
    """The async part of the launch command."""
    print("PLG CLI ready. Pinging the LLM...")
    llm_client = get_llm_client()
    response = await llm_client.acomplete(prompt="ping")

    if response and response.content:
        # Example of using the session to save something
        with get_session() as session:
            # In a real scenario, you would save a Decision or BranchNode here
            print(f"Database session is active: {session}")
        print(f"LLM response received: '{response.content[:10]}...'")
    else:
        print("Received no content from LLM.")


@app.command()
def launch():
    """
    Launches the Parallel Life Generator.

    Initializes the database automatically if it doesn't exist,
    then runs a test generation.
    """
    asyncio.run(_launch_async())


@app.command()
def collect():
    """
    Runs the interactive context collection tool and saves the results
    as a new Decision in the database.
    """
    context_data = collect_context()

    with get_session() as session:
        # Create the list of ContextBlock objects
        context_blocks = [
            ContextBlock(role=key, text=value) for key, value in context_data.items()
        ]

        # Create a parent Decision to link the context to
        new_decision = Decision(
            text="Initial context collected.", context_blocks=context_blocks
        )

        session.add(new_decision)
        session.commit()
        session.refresh(new_decision)

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


@app.command()
def hello(name: str):
    print(f"Hello {name}")


if __name__ == "__main__":
    app()
