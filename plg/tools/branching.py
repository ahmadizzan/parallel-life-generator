import json
from typing import List, TypedDict

from plg.llm.factory import get_llm_client
from plg.llm.prompts import BRANCH_GENERATION_PROMPT
from plg.models.models import ContextBlock
from plg.tools.parsing import extract_json_from_markdown


class Branch(TypedDict):
    decision: str
    tradeoffs: List[str]


async def generate_branches(
    parent_summary: str,
    context_blocks: List[ContextBlock],
    max_children: int,
) -> List[Branch]:
    """
    Generates a list of distinct, parallel next steps or paths based on a
    summary and context.

    Args:
        parent_summary: The summary of the parent node's decision.
        context_blocks: A list of ContextBlock objects providing the full context.
        max_children: The desired number of branches to generate.

    Returns:
        A list of Branch objects, where each object contains the decision
        text and a list of tradeoffs.
    """
    llm_client = get_llm_client()

    context_text = "\n".join(
        f"- {block.role.replace('_', ' ').title()}: {block.text}"
        for block in context_blocks
    )

    prompt = BRANCH_GENERATION_PROMPT.format(
        parent_summary=parent_summary,
        context_text=context_text,
        max_children=max_children,
    )

    response = await llm_client.acomplete(prompt=prompt)
    if not (response and response.content):
        return []

    json_content = extract_json_from_markdown(response.content) or response.content

    try:
        # The response should be a JSON string, so we parse it.
        branches = json.loads(json_content)
        # TODO: Add more robust validation here
        if isinstance(branches, list):
            return branches
        return []
    except json.JSONDecodeError:
        # The LLM failed to return valid JSON.
        return []
