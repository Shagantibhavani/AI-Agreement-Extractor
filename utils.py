import re
from datetime import datetime

def format_date(date_str):
    """
    Formats a date string into YYYY-MM-DD format.
    """
    if not date_str:
        return None
    try:
        # Attempt to parse common date formats
        date_obj = datetime.strptime(date_str, "%B %d, %Y")
        return date_obj.strftime("%Y-%m-%d")
    except ValueError:
        # Return the original string if parsing fails
        return date_str

def extract_clause(text, clause_title):
    """
    Extracts a specific clause from the text based on its title.
    This is a simple implementation and might need to be more robust.
    """
    # Pattern to find a clause by its title and capture the following paragraph
    pattern = re.compile(r"(\d+\.\s+{}\s*\.\s*)(.*?)(?=\n\d+\.\s+|\Z)".format(re.escape(clause_title)), re.DOTALL | re.IGNORECASE)
    match = pattern.search(text)
    
    if match:
        return match.group(2).strip()
    return None
