"""
Configuration file for the agreement extraction tool.
This file contains regular expression patterns for identifying key information.
"""

PATTERNS = {
    "parties": r"This Agreement is made between (.*?)\.",
    "effective_date": r"effective as of (.+?)\.",
    "risky_clauses": r"indemnify|liability|warranty",
    # Add more patterns as needed
}
