import json
import re
from datetime import datetime
import argparse

from config import PATTERNS
from utils import format_date, extract_clause

def extract_information(text):
    """
    Extracts structured information from the agreement text.
    """
    parties_match = re.search(PATTERNS["parties"], text, re.IGNORECASE)
    
    # Clean up party names
    cleaned_parties = []
    if parties_match:
        # This is a simple example; a real-world scenario would need more robust cleaning
        raw_parties = parties_match.group(1).split(' and ')
        for party in raw_parties:
            cleaned_parties.append(party.strip())
    
    effective_date_match = re.search(PATTERNS["effective_date"], text)
    effective_date = format_date(effective_date_match.group(1)) if effective_date_match else None

    termination_clause = extract_clause(text, "Termination")
    payment_terms = extract_clause(text, "Payment Terms")
    confidentiality_obligations = extract_clause(text, "Confidentiality")

    # A simple example of identifying risky clauses
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

def main():
    """
    Main function to run the extraction script.
    """
    parser = argparse.ArgumentParser(description="Extract structured information from a legal agreement.")
    parser.add_argument("file_path", help="Path to the agreement file.")
    args = parser.parse_args()

    try:
        with open(args.file_path, 'r') as f:
            agreement_text = f.read()
        
        extracted_data = extract_information(agreement_text)
        
        print(json.dumps(extracted_data, indent=2))

    except FileNotFoundError:
        print(f"Error: File not found at {args.file_path}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
