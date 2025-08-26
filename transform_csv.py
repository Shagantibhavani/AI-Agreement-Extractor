import csv
import json

def transform_data(json_file, output_file):
    """
    Transforms data from a JSON file to a CSV file with three columns:
    "Serial Number", "POLICY TERMS", and "DATA FROM THE AGREEMENT".
    """

    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: JSON file '{json_file}' not found.")
        return
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON format in '{json_file}': {e}")
        return

    transformed_data = []
    serial_number = 1  # Start at 1

    for agreement_term, extracted_data in data.items():
        # If the value is a list → join items with commas
        if isinstance(extracted_data, list):
            extracted_data = ", ".join(str(item) for item in extracted_data)

        # If the value is a dict → join key: value pairs
        elif isinstance(extracted_data, dict):
            extracted_data = "; ".join(f"{k}: {v}" for k, v in extracted_data.items())

        # Ensure it's a string
        extracted_data = str(extracted_data)

        transformed_data.append([serial_number, agreement_term, extracted_data])
        serial_number += 1

    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            csv_writer = csv.writer(csvfile)

            # Correct header
            csv_writer.writerow(["Serial Number", "POLICY TERMS", "DATA FROM THE AGREEMENT"])

            # Write rows
            csv_writer.writerows(transformed_data)

        print(f"✅ Successfully transformed data from '{json_file}' to '{output_file}'")

    except Exception as e:
        print(f"Error writing to CSV file: {e}")


if __name__ == '__main__':
    json_file = 'c:/Users/Dell/Downloads/extracted_data.json'  # Path to JSON file
    output_file = 'transformed_agreement_data.csv'
    transform_data(json_file, output_file)
