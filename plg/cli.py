import asyncio
import typer
from rich import print

from plg.llm.factory import get_llm_client
from plg.models.db import get_session


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
def hello(name: str):
    print(f"Hello {name}")


if __name__ == "__main__":
    app()
