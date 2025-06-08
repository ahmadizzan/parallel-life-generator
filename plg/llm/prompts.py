BRANCH_GENERATION_PROMPT = """
You are a creative strategist and life coach. Your task is to brainstorm the next set of sequential decision points or outcomes that would follow from a previous choice.

**Initial User Context:**
{context_text}

**The user has just made the following decision:**
{parent_summary}

Now, generate exactly {max_children} distinct, realistic, and actionable *next steps* or *consequences* that would logically follow. These should represent the next fork in the road after committing to the previous decision. They should not be variations of the parent decision, but what comes *after*.

For example, if the previous decision was 'Go part-time to write a novel,' good next steps could be:
- 'After six months, you realize your part-time income isn't enough. You could start teaching writing workshops to supplement it.'
- 'Your writing is gaining traction with short stories. You could apply for an MFA program to further develop your craft.'
- 'You are struggling with the discipline of writing alone. You could join a writer's group or hire a coach for accountability.'

For each generated path, provide a brief summary and a structured analysis of its tradeoffs.

Return your response as a single, flat JSON array of objects. Each object must have two keys: "decision" (a string) and "tradeoffs" (a list of strings).
Each tradeoff string must start with either "+" (for a positive tradeoff) or "-" (for a negative tradeoff).

Example format:
[
    {{
        "decision": "First possible path...",
        "tradeoffs": [
            "+ More creative freedom",
            "- Less stable income"
        ]
    }},
    {{
        "decision": "Second possible path...",
        "tradeoffs": [
            "+ Better work-life balance",
            "- Slower career progression"
        ]
    }}
]
"""

TAG_GENERATION_PROMPT = """
You are a strategic analyst and psychologist. Your task is to analyze the following proposed life path or decision and assign it tags for risk, growth potential, and emotional tone.

**Decision to Analyze:**
"{summary}"

**Instructions:**
1.  **Risk**: Assess the level of financial, social, or personal risk. Consider non-obvious risks. Rate it as "Low", "Medium", "High", or "Very High".
2.  **Growth Potential**: Assess the potential for personal or professional growth. Consider hidden opportunities. Rate it as "Low", "Medium", "High", or "Transformative".
3.  **Emotional Tone**: Describe the primary emotional tone of this path. Be realistic and nuanced. Use a single descriptive word. Examples: "Hopeful", "Anxious", "Torn", "Regretful", "Energized", "Pragmatic", "Adventurous", "Cautious".

Return your analysis as a single, flat JSON object. Do not include any other text, explanation, or markdown formatting.

Example format:
{{
  "risk": "Medium",
  "growth": "High",
  "emotion": "Ambitious"
}}
"""

CONTEXT_SUMMARY_PROMPT = """
Please synthesize the following points into a concise summary of the user's situation.
Focus on the key elements and desired outcome.

Context points:
{context_text}

Summary:
"""
