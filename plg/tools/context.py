from typing import List
from rich.prompt import Prompt

from plg.llm.factory import get_llm_client
from plg.models.models import ContextBlock


def collect_context() -> dict[str, str]:
    """
    Asks the user a series of open-ended questions to gather context
    and returns their answers as a dictionary.
    """
    print("Please answer the following questions to set the context.")

    questions = {
        "current_situation": "What is your current situation or challenge?",
        "ideal_outcome": "What is the ideal outcome you are aiming for?",
        "key_values": "What are your key values or principles in this situation?",
        "potential_obstacles": "What are the potential obstacles or constraints?",
        "available_resources": "What resources are available to you?",
    }

    answers = {}
    for key, question_text in questions.items():
        answers[key] = Prompt.ask(f"[bold yellow]?[/bold yellow] {question_text}")

    return answers


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
