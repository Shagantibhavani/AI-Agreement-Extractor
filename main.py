import os
import json
import argparse

from processors.text_processor import process_text
from processors.pdf_processor import process_pdf
from processors.word_processor import process_word
from processors.image_processor import process_image
from ai_analyzer import analyze_text_with_llm

def get_file_processor(file_path):
    """
    Determines the appropriate processor based on the file extension.
    """
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()

    if ext == '.txt':
        with open(file_path, 'r') as f:
            return f.read()
    elif ext == '.pdf':
        return process_pdf(file_path)
    elif ext == '.docx':
        return process_word(file_path)
    elif ext in ['.png', '.jpg', '.jpeg', '.tiff']:
        return process_image(file_path) # This will use the system PATH
    else:
        raise ValueError(f"Unsupported file type: {ext}")

def main():
    """
    Main function to run the enhanced extraction script.
    """
    parser = argparse.ArgumentParser(description="Extract structured information from a legal agreement.")
    parser.add_argument("file_path", help="Path to the agreement file.")
    parser.add_argument("--use_llm", action="store_true", help="Use LLM for analysis.")
    args = parser.parse_args()

    try:
        text = get_file_processor(args.file_path)
        
        if args.use_llm:
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY environment variable not set.")
            extracted_data = analyze_text_with_llm(text, api_key)
        else:
            extracted_data = process_text(text)
        
        print(json.dumps(extracted_data, indent=2))

    except (FileNotFoundError, ValueError, ImportError) as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
