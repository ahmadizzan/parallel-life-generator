import json
from typing import Dict, Any

from plg.llm.factory import get_llm_client


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

    prompt = f"""
You are a strategic analyst. Your task is to analyze the following proposed life path or decision and assign it tags for risk, growth potential, and emotional tone.

**Decision to Analyze:**
"{summary}"

**Instructions:**
1.  **Risk**: Assess the level of financial, social, or personal risk. Rate it as "Low", "Medium", or "High".
2.  **Growth Potential**: Assess the potential for personal or professional growth. Rate it as "Low", "Medium", or "High".
3.  **Emotional Tone**: Describe the primary emotional tone of this path. Use a single descriptive word (e.g., "Optimistic", "Cautious", "Ambitious", "Creative").

Return your analysis as a single, flat JSON object. Do not include any other text, explanation, or markdown formatting.

Example format:
{{
  "risk": "Medium",
  "growth": "High",
  "emotion": "Ambitious"
}}
"""
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
