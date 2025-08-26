import os
import json
import subprocess
import sys

def run_extraction(file_path, use_llm=False):
    """
    Runs the main.py script to extract information from a file.
    """
    command = [sys.executable, "main.py", file_path]
    if use_llm:
        command.append("--use_llm")
    
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        # The output from main.py is a JSON string, sometimes wrapped in an outer JSON object
        # if the LLM is used and it returns {"text": "..."}
        output_str = result.stdout.strip()
        try:
            parsed_output = json.loads(output_str)
            if isinstance(parsed_output, dict) and "text" in parsed_output:
                return json.loads(parsed_output["text"]) # Extract the inner JSON string
            return parsed_output
        except json.JSONDecodeError:
            return {"error": "Failed to parse main.py output", "raw_output": output_str}
    except subprocess.CalledProcessError as e:
        return {"error": f"Extraction failed: {e.stderr}", "raw_output": e.stdout}
    except Exception as e:
        return {"error": f"An unexpected error occurred during extraction: {e}"}

def compare_json_outputs(extracted_data, ground_truth):
    """
    Compares extracted data with ground truth and returns a score and discrepancies.
    """
    score = 0
    max_score = 0
    discrepancies = []

    # Fields that should match exactly (string comparison)
    exact_match_fields = [
        "effective_date", "termination_clause", "payment_terms",
        "confidentiality_obligations", "vendor", "receiver"
    ]

    for field in exact_match_fields:
        max_score += 1
        extracted_value = extracted_data.get(field)
        ground_value = ground_truth.get(field)

        if extracted_value == ground_value:
            score += 1
        else:
            discrepancies.append(f"Field '{field}': Expected '{ground_value}', Got '{extracted_value}'")
    
    # Parties (list of strings - order insensitive)
    max_score += 1
    extracted_parties = set(extracted_data.get("parties", []))
    ground_parties = set(ground_truth.get("parties", []))

    if extracted_parties == ground_parties:
        score += 1
    else:
        discrepancies.append(f"Field 'parties': Expected {list(ground_parties)}, Got {list(extracted_parties)}")

    # Risky Clauses (list of objects - compare 'clause_text', order insensitive)
    max_score += 1
    extracted_risky_clauses_raw = extracted_data.get("risky_clauses", [])
    ground_risky_clauses_raw = ground_truth.get("risky_clauses", [])

    # Handle cases where regex processor returns list of strings for risky_clauses
    if all(isinstance(item, str) for item in extracted_risky_clauses_raw):
        extracted_risky_clauses_set = set(extracted_risky_clauses_raw)
        ground_risky_clauses_set = {item.get("clause_text") for item in ground_risky_clauses_raw if isinstance(item, dict) and "clause_text" in item}
        
        if extracted_risky_clauses_set == ground_risky_clauses_set:
            score += 1
        else:
            discrepancies.append(f"Field 'risky_clauses': Expected clause texts {list(ground_risky_clauses_set)}, Got {list(extracted_risky_clauses_set)}")
    else: # Assume list of objects for LLM or correct format
        extracted_risky_clauses = {frozenset(item.items()) for item in extracted_risky_clauses_raw if isinstance(item, dict)}
        ground_risky_clauses = {frozenset(item.items()) for item in ground_risky_clauses_raw if isinstance(item, dict)}

        if extracted_risky_clauses == ground_risky_clauses:
            score += 1
        else:
            discrepancies.append(f"Field 'risky_clauses': Expected {list(ground_truth.get('risky_clauses', []))}, Got {list(extracted_data.get('risky_clauses', []))}")

    return score, max_score, discrepancies

def main():
    """
    Main function to run the evaluation script.
    """
    test_dir = "tests"
    if not os.path.exists(test_dir):
        print(f"Error: Test directory '{test_dir}' not found.")
        return

    total_tests = 0
    total_score_llm = 0
    total_max_score_llm = 0
    total_score_regex = 0
    total_max_score_regex = 0

    for entry in os.listdir(test_dir):
        case_path = os.path.join(test_dir, entry)
        if os.path.isdir(case_path):
            print(f"\n--- Evaluating Test Case: {entry} ---")
            agreement_file = None
            ground_truth_file = None

            for f in os.listdir(case_path):
                if f.endswith(('.txt', '.pdf', '.docx', '.png', '.jpg', '.jpeg', '.tiff')):
                    agreement_file = os.path.join(case_path, f)
                elif f == "ground_truth.json":
                    ground_truth_file = os.path.join(case_path, f)
            
            if not agreement_file:
                print(f"  No agreement file found in {case_path}. Skipping.")
                continue
            if not ground_truth_file:
                print(f"  No ground_truth.json found in {case_path}. Skipping.")
                continue

            total_tests += 1

            with open(ground_truth_file, 'r') as f:
                ground_truth = json.load(f)

            print(f"  Processing with LLM for {os.path.basename(agreement_file)}...")
            extracted_llm = run_extraction(agreement_file, use_llm=True)
            if "error" in extracted_llm:
                print(f"  LLM Extraction Error: {extracted_llm['error']}")
                if "raw_output" in extracted_llm:
                    print(f"  Raw Output: {extracted_llm['raw_output']}")
            else:
                score_llm, max_score_llm, discrepancies_llm = compare_json_outputs(extracted_llm, ground_truth)
                total_score_llm += score_llm
                total_max_score_llm += max_score_llm
                print(f"  LLM Score: {score_llm}/{max_score_llm}")
                if discrepancies_llm:
                    print("  LLM Discrepancies:")
                    for d in discrepancies_llm:
                        print(f"    - {d}")

            print(f"  Processing with Regex for {os.path.basename(agreement_file)}...")
            extracted_regex = run_extraction(agreement_file, use_llm=False)
            if "error" in extracted_regex:
                print(f"  Regex Extraction Error: {extracted_regex['error']}")
                if "raw_output" in extracted_regex:
                    print(f"  Raw Output: {extracted_regex['raw_output']}")
            else:
                score_regex, max_score_regex, discrepancies_regex = compare_json_outputs(extracted_regex, ground_truth)
                total_score_regex += score_regex
                total_max_score_regex += max_score_regex
                print(f"  Regex Score: {score_regex}/{max_score_regex}")
                if discrepancies_regex:
                    print("  Regex Discrepancies:")
                    for d in discrepancies_regex:
                        print(f"    - {d}")
    
    print("\n--- Overall Results ---")
    if total_tests > 0:
        print(f"Total Test Cases: {total_tests}")
        if total_max_score_llm > 0:
            print(f"Overall LLM Score: {total_score_llm}/{total_max_score_llm} ({total_score_llm/total_max_score_llm:.2f}%)")
        else:
            print("Overall LLM Score: N/A (No LLM tests run or all failed)")
        
        if total_max_score_regex > 0:
            print(f"Overall Regex Score: {total_score_regex}/{total_max_score_regex} ({total_score_regex/total_max_score_regex:.2f}%)")
        else:
            print("Overall Regex Score: N/A (No Regex tests run or all failed)")
    else:
        print("No test cases found.")

if __name__ == "__main__":
    main()
