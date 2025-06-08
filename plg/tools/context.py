from typing import List
import typer
from rich import print
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from plg.llm.factory import get_llm_client
from plg.models.models import ContextBlock

console = Console()

DEFAULT_CONTEXT_QUESTIONS = {
    "core_desire": "What is the core desire or goal you want to achieve?",
    "current_situation": "Briefly describe your current situation and why you're considering a change.",
    "key_constraints": "What are the key constraints or non-negotiables (e.g., financial, geographical, personal)?",
    "relevant_skills": "What are your relevant skills, resources, or strengths that could help you?",
    "ideal_outcome": "In an ideal world, what would the perfect outcome look like in 5 years?",
}


def collect_context() -> dict:
    """
    Interactively collects context from the user by asking a series of questions.
    """
    print(
        Panel(
            Markdown(
                """
# Welcome to the Context Collector!

Please answer the following questions to help generate your parallel life paths.
Be as detailed as you feel necessary.
"""
            ),
            title="[bold cyan]Parallel Life Generator[/bold cyan]",
            border_style="cyan",
        )
    )

    context_data = {}
    for key, question in DEFAULT_CONTEXT_QUESTIONS.items():
        response = typer.prompt(f"[bold yellow]?[/bold yellow] {question}")
        context_data[key] = response

    return context_data


async def summarise_context(context_blocks: List[ContextBlock]) -> str:
    """
    Takes a list of ContextBlock objects, formats them into a prompt,
    and calls the LLM to generate a concise summary.

    Args:
        context_blocks: A list of ContextBlock objects containing the
                        context to be summarized.

    Returns:
        A string containing the LLM-generated summary.
    """
    llm_client = get_llm_client()

    # Format the context blocks into a single prompt for the LLM
    context_text = "\n".join(
        f"- {block.role.replace('_', ' ').title()}: {block.text}"
        for block in context_blocks
    )
    prompt = f"""
Please synthesize the following points into a concise summary of the user's situation.
Focus on the key elements and desired outcome.

Context points:
{context_text}

Summary:
"""

    response = await llm_client.acomplete(prompt=prompt)

    if response and response.content:
        return response.content.strip()

    return "No summary could be generated."
