import os
import json

try:
    import google.generativeai as genai
except ImportError:
    genai = None

def analyze_text_with_llm(text, api_key):
    """
    Analyzes text using the Gemini LLM to extract structured information and token usage.
    """
    if not genai:
        raise ImportError("google-generativeai is not installed. Please install it with 'pip install google-generativeai'")

    genai.configure(api_key="AIzaSyAA7Lcm03baxHKi7vy9Ebgj7usfypC5yqQ")

    model = genai.GenerativeModel('gemini-1.5-flash')

    # --- MODIFICATION: Updated prompt to include vendor and receiver ---
    # --- MODIFICATION: Enhanced prompt for risky_clauses to be more specific and include examples ---
    # --- MODIFICATION: Added instruction for LLM to explain why a clause is risky ---
    prompt = f"""
    You are a highly skilled legal document analyst. Your task is to extract specific information from the provided agreement text.
    First, carefully read and understand the entire agreement.
    Then, extract the following fields. If a field is not explicitly present or cannot be reasonably inferred, use `null`.

    - parties (as a JSON array of strings, identifying all entities involved in the agreement, e.g., "City of Olympia", "Consultant Name". Be precise.)
    - effective_date (YYYY-MM-DD format if a specific date is given, otherwise provide the exact text describing the effective date, e.g., "2025-01-15" or "as of the date of the last authorizing signature affixed hereto". Do not infer a date if not explicitly stated.)
    - termination_clause (the full and exact text of the section(s) detailing termination conditions, notice periods, and any associated penalties or obligations. If multiple sections relate to termination, combine them.)
    - payment_terms (the full and exact text of the section(s) detailing compensation, fees, invoicing, payment schedules, due dates, and any tax responsibilities. If multiple sections relate to payment, combine them.)
    - confidentiality_obligations (the full and exact text of the section(s) outlining confidentiality, non-disclosure, and data protection requirements. If multiple sections relate to confidentiality, combine them.)
    - risky_clauses (as a JSON array of objects. Each object must have two keys: "clause_text" (the exact text of the clause) and "explanation" (a brief, clear explanation of why it is considered risky, unusual, or potentially problematic for either party). Focus on clauses that:
        - Limit liability significantly (e.g., "neither party shall be liable for indirect damages").
        - Impose broad indemnification obligations.
        - Include penalties for early termination.
        - Have unusual or ambiguous payment terms.
        - Grant broad exclusivity.
        - Appear one-sided or overly restrictive.
        - Contain vague or unclear language that could lead to disputes.
        If the Effective Date is not explicitly specified, flag this as a risky clause.
        If the Termination Clause is not detailed, flag this as a risky clause.
        Example of a risky clause object:
        {{
          "clause_text": "Neither party shall be liable for any indirect, incidental, special, consequential or punitive damages...",
          "explanation": "This clause limits the liability of both parties, preventing recovery of significant categories of damages. This could be risky for the City if it relies on the Consultant's services and suffers substantial indirect losses due to the Consultant's failure."
        }}
        Ensure the "explanation" clearly articulates the potential risk.
        If no risky clauses are found, return an empty array `[]`.)
    - vendor (the name of the entity providing services or goods. In a "Professional Services Agreement," this is typically the "Consultant." Extract the full, formal name if available. If not explicitly named, infer from context, but prioritize explicit mentions.)
    - receiver (the name of the entity receiving services or goods. In a "Professional Services Agreement," this is typically the "City" or "Client." Extract the full, formal name if available. If not explicitly named, infer from context, but prioritize explicit mentions.)

    Also, extract the following with high precision:
    - effective_date (YYYY-MM-DD format if a specific date is given, otherwise provide the exact text describing the effective date, e.g., "2025-01-15" or "as of the date of the last authorizing signature affixed hereto". Do not infer a date if not explicitly stated.)
    - termination_clause (the full and exact text of the section(s) detailing termination conditions, notice periods, and any associated penalties or obligations. If multiple sections relate to termination, combine them.)

    Return the output strictly in JSON format. Do not include any additional text or markdown outside the JSON object. Ensure the JSON is valid and complete.

    Agreement text:
    {text}
    """

    response = model.generate_content(prompt)

    # Capture token usage
    token_usage = {
        "input_tokens": response.usage_metadata.prompt_token_count,
        "output_tokens": response.usage_metadata.candidates_token_count,
        "total_tokens": response.usage_metadata.total_token_count
    }

    # The response from Gemini might need to be cleaned up to be valid JSON
    cleaned_text = response.text.strip().replace('```json', '').replace('```', '').strip()
    
    extracted_data = {}
    try:
        extracted_data = json.loads(cleaned_text)
    except (json.JSONDecodeError, AttributeError):
        # If JSON parsing fails, try to extract specific fields if possible, or return error
        # For now, we'll return an error and the raw response.
        # A more robust solution might involve more sophisticated error handling or regex extraction.
        return {"error": "Failed to parse LLM response", "raw_response": response.text if hasattr(response, 'text') else str(response)}

    # --- MODIFICATION: Post-process to ensure all expected fields are lists or null ---
    expected_fields = [
        "parties", "effective_date", "termination_clause", 
        "payment_terms", "confidentiality_obligations", 
        "risky_clauses", "vendor", "receiver"
    ]

    for field in expected_fields:
        if field not in extracted_data or extracted_data[field] is None:
            if field in ["parties", "risky_clauses"]:
                extracted_data[field] = [] # Default to empty list for these fields
            else:
                extracted_data[field] = None # Default to null for others
        else:
            # Ensure specific fields are lists
            if field in ["parties", "risky_clauses"]:
                if isinstance(extracted_data[field], str):
                    try:
                        # Try to parse if it's a string representation of a list
                        parsed_list = json.loads(extracted_data[field])
                        if isinstance(parsed_list, list):
                            extracted_data[field] = parsed_list
                        else:
                            extracted_data[field] = [extracted_data[field]] # Treat as single item if not a list
                    except json.JSONDecodeError:
                        extracted_data[field] = [extracted_data[field]] # Treat as single item if not valid JSON
                elif not isinstance(extracted_data[field], list):
                    extracted_data[field] = [str(extracted_data[field])] # Ensure it's a list of strings
            # For other fields, ensure they are strings or null
            elif not isinstance(extracted_data[field], str) and extracted_data[field] is not None:
                 extracted_data[field] = str(extracted_data[field])

    return {
        "text": json.dumps(extracted_data, indent=2)
    }
