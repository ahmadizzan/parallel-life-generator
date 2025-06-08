import re
from typing import Optional


def find_year_in_text(text: str) -> Optional[int]:
    """
    Finds the first 4-digit year (19xx or 20xx) in a string.

    Args:
        text: The string to search.

    Returns:
        The year as an integer, or None if not found.
    """
    # Regex to find a 4-digit number that looks like a year from 1900-2099
    match = re.search(r"\b(19|20)\d{2}\b", text)
    if match:
        return int(match.group(0))
    return None
