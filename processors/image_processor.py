try:
    from PIL import Image, ImageEnhance
    import pytesseract
except ImportError:
    Image = None
    pytesseract = None

def process_image(file_path, tesseract_cmd=None):
    """
    Processes an image file to extract text using OCR.
    """
    if not Image or not pytesseract:
        raise ImportError("Pillow and pytesseract are not installed. Please install them with 'pip install Pillow pytesseract'")

    if tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    try:
        image = Image.open(file_path)
        # Convert to grayscale
        image = image.convert('L')
        # Increase contrast
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2)
        text = pytesseract.image_to_string(image)
        # Basic text cleaning
        text = text.replace('\n', ' ').replace('\r', '')  # Remove newlines
        text = ' '.join(text.split())  # Remove extra whitespace
        return text
    except pytesseract.TesseractNotFoundError:
        raise ValueError(
            "Tesseract is not installed or it's not in your PATH."
            "See README file for more information."
        )
