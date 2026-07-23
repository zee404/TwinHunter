import hashlib
import os
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Callable, Optional

import imagehash
from PIL import Image, ImageOps


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tif", ".tiff", ".webp"}


class ScanCancelled(Exception):
    """Raised when the user cancels a running scan."""


@dataclass(frozen=True)
class VisualFingerprint:
    """Complementary hashes used to compare visual content."""

    phash: Any
    whash: Any
    colorhash: Any


class ImageScanner:
    """Find byte-identical files or visually similar images."""

    def __init__(self):
        self.duplicates = {}
        self.skipped_files = []

    @staticmethod
    def calculate_exact_hash(image_path: str) -> str:
        digest = hashlib.sha256()
        with open(image_path, "rb") as image_file:
            for chunk in iter(lambda: image_file.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    @staticmethod
    def calculate_visual_fingerprint(image_path: str) -> VisualFingerprint:
        with Image.open(image_path) as image:
            # Apply camera orientation and ignore animation frames after the first.
            normalized = ImageOps.exif_transpose(image).convert("RGB")
            return VisualFingerprint(
                phash=imagehash.phash(normalized, hash_size=16),
                whash=imagehash.whash(normalized, hash_size=16),
                colorhash=imagehash.colorhash(normalized, binbits=3),
            )

    @staticmethod
    def similarity_score(left: VisualFingerprint, right: VisualFingerprint) -> float:
        """Return a 0-100 visual similarity score.

        Perceptual and wavelet hashes capture structure while colorhash helps
        distinguish similarly shaped scenes with different colour distributions.
        """
        phash_similarity = 1.0 - (left.phash - right.phash) / left.phash.hash.size
        whash_similarity = 1.0 - (left.whash - right.whash) / left.whash.hash.size
        color_similarity = 1.0 - (left.colorhash - right.colorhash) / left.colorhash.hash.size
        score = (0.60 * phash_similarity) + (0.25 * whash_similarity) + (0.15 * color_similarity)
        return max(0.0, min(100.0, score * 100.0))

    @staticmethod
    def _collect_images(
        folder_path: str,
        discovery_callback=None,
        cancel_check=None,
    ) -> list[str]:
        if not os.path.isdir(folder_path):
            raise ValueError("The selected folder no longer exists or is not accessible.")

        image_files = []
        for root, dirs, files in os.walk(folder_path):
            ImageScanner._check_cancelled(cancel_check)
            dirs.sort(key=str.casefold)
            for filename in sorted(files, key=str.casefold):
                if os.path.splitext(filename)[1].lower() in IMAGE_EXTENSIONS:
                    image_files.append(os.path.join(root, filename))
            if discovery_callback:
                discovery_callback(len(image_files), root)
        return image_files

    @staticmethod
    def _check_cancelled(cancel_check: Optional[Callable[[], bool]]) -> None:
        if cancel_check and cancel_check():
            raise ScanCancelled()

    def scan_directory(
        self,
        folder_path,
        callback=None,
        similarity=100,
        cancel_check=None,
        discovery_callback=None,
    ):
        """Scan a folder recursively.

        ``similarity=100`` uses SHA-256 and returns only byte-identical files.
        Lower values use visual fingerprints; 85 is a useful balanced default.
        """
        if not 0 <= similarity <= 100:
            raise ValueError("Similarity must be between 0 and 100.")

        image_files = self._collect_images(folder_path, discovery_callback, cancel_check)
        total_files = len(image_files)
        self.skipped_files = []
        self._check_cancelled(cancel_check)

        if similarity == 100:
            # Size is a cheap pre-filter. Only same-sized files can be byte-identical.
            files_by_size = defaultdict(list)
            for path in image_files:
                try:
                    files_by_size[os.path.getsize(path)].append(path)
                except OSError as error:
                    self.skipped_files.append((path, str(error)))

            candidates = {path for paths in files_by_size.values() if len(paths) > 1 for path in paths}
            hashes = defaultdict(list)
            for index, path in enumerate(image_files, start=1):
                self._check_cancelled(cancel_check)
                if callback:
                    callback(index, total_files, path)
                if path not in candidates:
                    continue
                try:
                    hashes[self.calculate_exact_hash(path)].append(path)
                except OSError as error:
                    self.skipped_files.append((path, str(error)))
            self.duplicates = {key: paths for key, paths in hashes.items() if len(paths) > 1}
            return self.duplicates

        fingerprints = []
        for index, path in enumerate(image_files, start=1):
            self._check_cancelled(cancel_check)
            if callback:
                callback(index, total_files, path)
            try:
                fingerprints.append((path, self.calculate_visual_fingerprint(path)))
            except (OSError, ValueError, Image.DecompressionBombError) as error:
                self.skipped_files.append((path, str(error)))

        # Build deterministic connected components of all matching pairs. This
        # includes chains of related edits rather than depending on os.walk order.
        parent = list(range(len(fingerprints)))

        def find(item):
            while parent[item] != item:
                parent[item] = parent[parent[item]]
                item = parent[item]
            return item

        def union(left, right):
            left_root, right_root = find(left), find(right)
            if left_root != right_root:
                parent[right_root] = left_root

        for left in range(len(fingerprints)):
            self._check_cancelled(cancel_check)
            for right in range(left + 1, len(fingerprints)):
                if self.similarity_score(fingerprints[left][1], fingerprints[right][1]) >= similarity:
                    union(left, right)

        groups = defaultdict(list)
        for index, (path, _) in enumerate(fingerprints):
            groups[find(index)].append(path)
        self.duplicates = {
            f"similar_{group_number}": paths
            for group_number, paths in enumerate(groups.values(), start=1)
            if len(paths) > 1
        }
        return self.duplicates
