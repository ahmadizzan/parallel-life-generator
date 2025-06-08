import asyncio
import typer
from rich import print

from plg.llm.factory import get_llm_client


app = typer.Typer()


async def _launch_async():
    """The async part of the launch command."""
    print("PLG CLI ready. Pinging the LLM...")
    llm_client = get_llm_client()
    response = await llm_client.acomplete(prompt="ping")

    if response and response.content:
        print(f"LLM response received: '{response.content[:10]}...'")
    else:
        print("Received no content from LLM.")


@app.command()
def launch():
    """Launches the Parallel Life Generator and runs a test generation."""
    asyncio.run(_launch_async())


@app.command()
def hello(name: str):
    print(f"Hello {name}")


if __name__ == "__main__":
    app()
