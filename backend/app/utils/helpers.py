import os
from datetime import datetime

def get_file_info(file_path: str) -> dict:
    return {
        "filename": os.path.basename(file_path),
        "size": os.path.getsize(file_path),
        "extension": os.path.splitext(file_path)[1],
        "modified": datetime.fromtimestamp(
            os.path.getmtime(file_path)
        ).isoformat()
    }

def format_file_size(size_bytes: int) -> str:
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"
