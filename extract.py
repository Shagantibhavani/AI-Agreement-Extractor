import json
import re
from ai_analyzer import analyze_text_with_llm # Import the LLM analysis function

def extract_data():
    """
    Extracts data from a sample agreement text using LLM analysis
    and returns it in the desired JSON format.
    """
    sample_agreement_text = """Sample Agreement
1. Parties
This Agreement is made between Party A ("Provider") and Party B ("Client") for the purpose of providing services as described herein.
2. Terms
The Agreement shall commence on the Effective Date and continue for a period of one year, unless terminated earlier in accordance with the provisions of this Agreement.
3. Payment
The Client agrees to pay the Provider the fees as specified in the attached schedule. Payments are due within 30 days of invoice.
4. Confidentiality
Both parties agree to keep confidential all information disclosed during the term of this Agreement.
5. Signatures
Party A: ____________________
Party B: ____________________"""

    # Use the LLM to analyze the text and extract structured data
    # The API key is now hardcoded in ai_analyzer.py, so we pass a dummy value here.
    llm_analysis_result = analyze_text_with_llm(sample_agreement_text, "dummy_api_key")

    if "error" in llm_analysis_result:
        print(f"Error during LLM analysis: {llm_analysis_result['error']}")
        return {}
    
    # The LLM returns a JSON string in the 'text' field
    extracted_data = json.loads(llm_analysis_result["text"])

    # Map the LLM output keys to the desired output keys for the CSV
    # This step is crucial to ensure the CSV headers match the user's request
    final_data = {
        "Parties Involved": extracted_data.get("parties", "Not specified"),
        "Effective Date": extracted_data.get("effective_date", "Not specified"),
        "Termination Clauses": extracted_data.get("termination_clause", "Not specified"),
        "Payment Terms": extracted_data.get("payment_terms", "Not specified"),
        "Confidentiality Obligations": extracted_data.get("confidentiality_obligations", "Not specified"),
        "Risky/Unusual Clauses": extracted_data.get("risky_clauses", []),
        "Vendor": extracted_data.get("vendor", "Not specified"),
        "Receiver": extracted_data.get("receiver", "Not specified")
    }

    return final_data

if __name__ == '__main__':
    extracted_data = extract_data()

    # Save the extracted data to a JSON file
    with open('../../Downloads/extracted_data.json', 'w', encoding='utf-8') as f:
        json.dump(extracted_data, f, indent=2)

    print("Extracted data saved to ../../Downloads/extracted_data.json")
