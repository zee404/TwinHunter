import os
import imagehash
from PIL import Image
from collections import defaultdict

class ImageScanner:
    def __init__(self):
        self.duplicates = defaultdict(list)

    def calculate_hash(self, image_path):
        try:
            with Image.open(image_path) as img:
                # Revert to phash as it is more robust for perceptual duplicates
                return str(imagehash.phash(img))
        except Exception as e:
            print(f"Error hashing {image_path}: {e}")
            return None

    def scan_directory(self, folder_path, callback=None):
        """
        Scans the directory for images and finds duplicates.
        :param folder_path: Path to the folder to scan.
        :param callback: Optional callback function to report progress (current_file, total_files).
        """
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp'}
        image_files = []

        # First pass: collect all image files
        for root, _, files in os.walk(folder_path):
            for file in files:
                if os.path.splitext(file)[1].lower() in image_extensions:
                    image_files.append(os.path.join(root, file))

        total_files = len(image_files)
        hashes = {}
        
        for i, file_path in enumerate(image_files):
            if callback:
                callback(i + 1, total_files, file_path)
            
            img_hash = self.calculate_hash(file_path)
            if img_hash:
                if img_hash in hashes:
                    hashes[img_hash].append(file_path)
                else:
                    hashes[img_hash] = [file_path]

        # Filter out unique images
        self.duplicates = {k: v for k, v in hashes.items() if len(v) > 1}
        return self.duplicates
