import zipfile
import py7zr
import os
from django.conf import settings


def extract_archive(file_path, target_dir):
    os.makedirs(target_dir, exist_ok=True)
    
    if file_path.endswith('.zip'):
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(target_dir)
    elif file_path.endswith('.7z'):
        with py7zr.SevenZipFile(file_path, mode='r') as z:
            z.extractall(target_dir)
    
    find_and_move_index_html(target_dir)


def find_and_move_index_html(directory):
    index_path = None
    for root, dirs, files in os.walk(directory):
        if 'index.html' in files:
            index_path = os.path.join(root, 'index.html')
            break
    
    if index_path:
        parent_dir = os.path.dirname(index_path)
        if parent_dir != directory:
            for item in os.listdir(parent_dir):
                src = os.path.join(parent_dir, item)
                dst = os.path.join(directory, item)
                if not os.path.exists(dst):
                    if os.path.isdir(src):
                        import shutil
                        shutil.move(src, dst)
                    else:
                        os.rename(src, dst)
            os.rmdir(parent_dir)
