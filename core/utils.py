import os
import send2trash

def format_size(size_bytes):
    """Formats file size in bytes to human readable string."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"

def safe_delete(file_path):
    """Sends the file to the recycle bin."""
    try:
        # Normalize path to fix mixed slashes and ensure absolute path
        file_path = os.path.normpath(os.path.abspath(file_path))
        send2trash.send2trash(file_path)
        return True
    except Exception as e:
        print(f"Error deleting {file_path}: {e}")
        return False

def get_file_size(file_path):
    """Returns file size in bytes."""
    try:
        return os.path.getsize(file_path)
    except OSError:
        return 0
