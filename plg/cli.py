import asyncio
import typer
from rich import print

from plg.llm.factory import get_llm_client
from plg.models.db import get_session
from plg.models.models import ContextBlock, Decision
from plg.tools.context import collect_context, summarise_context


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
            return

        summary = await summarise_context(decision.context_blocks)
        print("\n[bold green]Generated Summary:[/bold green]")
        print(summary)


@app.command()
def summarise(
    decision_id: int = typer.Argument(..., help="The ID of the decision to summarise.")
):
    """
    Summarises the context associated with a given Decision ID.
    """
    asyncio.run(_summarise_async(decision_id))


@app.command()
def hello(name: str):
    print(f"Hello {name}")


if __name__ == "__main__":
    app()
