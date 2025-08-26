import re
from config import PATTERNS
from utils import format_date, extract_clause

def process_text(text):
    """
    Processes plain text to extract agreement information.
    """
    parties_match = re.search(PATTERNS["parties"], text, re.IGNORECASE)
    
    cleaned_parties = []
    if parties_match:
        raw_parties = parties_match.group(1).split(' and ')
        for party in raw_parties:
            cleaned_parties.append(party.strip())
    
    effective_date_match = re.search(PATTERNS["effective_date"], text)
    effective_date = format_date(effective_date_match.group(1)) if effective_date_match else None

    termination_clause = extract_clause(text, "Termination")
    payment_terms = extract_clause(text, "Payment Terms")
    confidentiality_obligations = extract_clause(text, "Confidentiality")

    risky_clauses = []
    for clause in re.finditer(PATTERNS["risky_clauses"], text, re.IGNORECASE):
        risky_clauses.append(clause.group(0).strip())

    return {
        "parties": cleaned_parties if cleaned_parties else None,
        "effective_date": effective_date,
        "termination_clause": termination_clause,
        "payment_terms": payment_terms,
        "confidentiality_obligations": confidentiality_obligations,
        "risky_clauses": risky_clauses if risky_clauses else None
    }
