# validators.py
from django.core.exceptions import ValidationError
import os

def validate_file_extension(value):
    ext = os.path.splitext(value.name)[1]  # Get the file extension
    valid_extensions = ['.pdf']
    if ext.lower() not in valid_extensions:
        raise ValidationError('Unsupported file extension. Only PDF files are allowed.')
