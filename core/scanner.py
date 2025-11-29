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

    def scan_directory(self, folder_path, callback=None, threshold=0):
        """
        Scans the directory for images and finds duplicates.
        :param folder_path: Path to the folder to scan.
        :param callback: Optional callback function to report progress (current_file, total_files).
        :param threshold: Hamming distance threshold (0 for exact match).
        """
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp'}
        image_files = []

        # First pass: collect all image files
        for root, _, files in os.walk(folder_path):
            for file in files:
                if os.path.splitext(file)[1].lower() in image_extensions:
                    image_files.append(os.path.join(root, file))

        total_files = len(image_files)
        
        # Store (path, hash_obj) tuples
        hashed_images = []
        
        for i, file_path in enumerate(image_files):
            if callback:
                callback(i + 1, total_files, file_path)
            
            img_hash_str = self.calculate_hash(file_path)
            if img_hash_str:
                # Convert back to hash object for comparison if needed, 
                # but calculate_hash returns string. 
                # We can reconstruct it using imagehash.hex_to_hash
                try:
                    hash_obj = imagehash.hex_to_hash(img_hash_str)
                    hashed_images.append((file_path, hash_obj))
                except:
                    pass

        # Grouping Logic
        self.duplicates = {}
        
        if threshold == 0:
            # Fast exact matching
            hashes = defaultdict(list)
            for file_path, hash_obj in hashed_images:
                hashes[str(hash_obj)].append(file_path)
            self.duplicates = {k: v for k, v in hashes.items() if len(v) > 1}
        else:
            # Fuzzy matching (Greedy Clustering)
            # This is O(N^2) in worst case, but N is usually small (<10k)
            visited = set()
            group_id = 0
            
            for i in range(len(hashed_images)):
                if i in visited:
                    continue
                    
                path_i, hash_i = hashed_images[i]
                current_group = [path_i]
                visited.add(i)
                
                for j in range(i + 1, len(hashed_images)):
                    if j in visited:
                        continue
                        
                    path_j, hash_j = hashed_images[j]
                    
                    # Calculate Hamming distance
                    if hash_i - hash_j <= threshold:
                        current_group.append(path_j)
                        visited.add(j)
                
                if len(current_group) > 1:
                    # Use the hash of the first image as key (or a unique ID)
                    self.duplicates[f"group_{group_id}_{str(hash_i)}"] = current_group
                    group_id += 1

        return self.duplicates
