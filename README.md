# AI-Powered Agreement Extraction Tool

This script extracts structured information from legal agreements in various formats (PDF, Word, TXT, images).

## Features

- **Web-Based UI**: An easy-to-use interface built with Streamlit.
- **Multi-Format Support**: Handles PDF, Word, plain text, and image files.
- **AI-Powered Analysis**: Uses Google's Gemini LLM for more accurate and context-aware extraction.
- **Secure API Key Storage**: Uses Streamlit's secrets management to keep your API key safe.

## Installation

1.  **Install Tesseract OCR Engine (for image processing):**
    -   Download the Tesseract installer for Windows from the [Tesseract at UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki) page.
    -   Run the installer. **Important:** During installation, make sure to check the option "Add Tesseract to system PATH". If you don't add it to PATH, you'll need to specify the full path in `.streamlit/secrets.toml`.
    -   After installation, you may need to restart your computer for the PATH changes to take effect.

2.  **Install the required Python packages:**

    ```bash
    pip install -r requirements.txt
    ```

3.  **Add your API keys and Tesseract path to the secrets file:**
    -   Open the `.streamlit/secrets.toml` file.
    -   Replace `"your_api_key_here"` with your actual Gemini API key.
    -   If Tesseract is not in your system PATH, replace `"your_tesseract_path_here"` with the full path to your `tesseract.exe` (e.g., `C:\Program Files\Tesseract-OCR\tesseract.exe`).

## Usage

### Streamlit Web App

To run the web app, use the following command:

```bash
streamlit run app.py
```

### Command-Line Interface

The command-line interface is still available but does not support the LLM functionality without setting the `GEMINI_API_KEY` environment variable manually.

```bash
python main.py <path_to_agreement_file>
```

## Output

The script will output a JSON object with the extracted information.
