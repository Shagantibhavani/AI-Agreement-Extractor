try:
    import docx
except ImportError:
    docx = None

def process_word(file_path):
    """
    Processes a Word document to extract text.
    """
    if not docx:
        raise ImportError("python-docx is not installed. Please install it with 'pip install python-docx'")

    doc = docx.Document(file_path)
    text = ""
    for para in doc.paragraphs:
        text += para.text + "\n"
    return text
