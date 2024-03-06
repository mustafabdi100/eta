# utils.py
import os
from django.core.files.storage import default_storage

def ensure_tmp_directory_exists():
    tmp_directory = os.path.join(default_storage.location, 'tmp')
    os.makedirs(tmp_directory, exist_ok=True)
