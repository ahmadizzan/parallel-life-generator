import json
from typing import List

from plg.llm.factory import get_llm_client
from plg.models.models import ContextBlock


async def generate_branches(
    parent_summary: str,
    context_blocks: List[ContextBlock],
    depth: int,
    max_children: int,
) -> List[str]:
    """
    Generates a list of distinct, parallel next steps or paths based on a
    summary and context.

    Args:
        parent_summary: The summary of the parent node's decision.
        context_blocks: A list of ContextBlock objects providing the full context.
        depth: The current depth in the decision tree.
        max_children: The desired number of branches to generate.

    Returns:
        A list of strings, where each string is a generated branch or path.
    """
    llm_client = get_llm_client()

    context_text = "\n".join(
        f"- {block.role.replace('_', ' ').title()}: {block.text}"
        for block in context_blocks
    )

    prompt = f"""
You are a creative strategist and life coach. Your task is to brainstorm parallel possibilities based on a user's situation.

**Current Situation Summary:**
{parent_summary}

**Full Context:**
{context_text}

Based on the situation, generate exactly {max_children} distinct, creative, and actionable future paths or alternative next steps.
These paths should be mutually exclusive where possible.

Return your response as a single, flat JSON array of strings. Do not include any other text, explanation, or markdown formatting.

Example format:
["First possible path...", "Second possible path...", "Third possible path..."]
"""

    response = await llm_client.acomplete(prompt=prompt)
    if not (response and response.content):
        return []

    try:
        # The response should be a JSON string, so we parse it.
        branches = json.loads(response.content)
        if isinstance(branches, list) and all(isinstance(i, str) for i in branches):
            return branches
        return []
    except json.JSONDecodeError:
        # The LLM failed to return valid JSON.
        return []
