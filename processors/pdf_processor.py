try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

def process_pdf(file_path):
    """
    Processes a PDF file to extract text.
    """
    if not PyPDF2:
        raise ImportError("PyPDF2 is not installed. Please install it with 'pip install PyPDF2'")
        
    text = ""
    with open(file_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            text += page.extract_text()
    return text
