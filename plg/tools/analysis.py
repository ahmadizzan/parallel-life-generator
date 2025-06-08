import json
from typing import Dict, Any

from plg.llm.factory import get_llm_client
from plg.llm.prompts import TAG_GENERATION_PROMPT


async def annotate_branch(summary: str) -> Dict[str, Any]:
    """
    Analyzes a branch summary using an LLM to assess its risk, growth
    potential, and emotional tone.

    Args:
        summary: The text of the branch decision to analyze.

    Returns:
        A dictionary containing the analysis tags.
    """
    llm_client = get_llm_client()

    prompt = TAG_GENERATION_PROMPT.format(summary=summary)

    response = await llm_client.acomplete(prompt=prompt)
    if not (response and response.content):
        return {}

    try:
        annotations = json.loads(response.content)
        if isinstance(annotations, dict):
            return annotations
        return {}
    except json.JSONDecodeError:
        return {}
