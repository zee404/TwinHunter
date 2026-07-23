import os
import shutil
import tempfile
import unittest

from PIL import Image, ImageDraw, ImageEnhance

from core.scanner import ImageScanner, ScanCancelled
from core.utils import format_size, get_image_quality


class TestCore(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="twinhunter_")
        self.original = os.path.join(self.test_dir, "original.png")
        image = Image.new("RGB", (160, 100), "navy")
        draw = ImageDraw.Draw(image)
        draw.rectangle((10, 10, 75, 90), fill="white")
        draw.ellipse((90, 20, 145, 80), fill="orange")
        image.save(self.original)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_exact_mode_finds_only_byte_identical_files(self):
        copy = os.path.join(self.test_dir, "copy.png")
        reencoded = os.path.join(self.test_dir, "reencoded.bmp")
        shutil.copy2(self.original, copy)
        with Image.open(self.original) as image:
            image.save(reencoded)

        duplicates = ImageScanner().scan_directory(self.test_dir, similarity=100)
        self.assertEqual(1, len(duplicates))
        self.assertEqual({self.original, copy}, set(next(iter(duplicates.values()))))

    def test_similar_mode_finds_reencoded_and_adjusted_images(self):
        reencoded = os.path.join(self.test_dir, "reencoded.jpg")
        brighter = os.path.join(self.test_dir, "brighter.png")
        with Image.open(self.original) as image:
            image.save(reencoded, quality=90)
            ImageEnhance.Brightness(image).enhance(1.1).save(brighter)

        duplicates = ImageScanner().scan_directory(self.test_dir, similarity=85)
        matched = {path for group in duplicates.values() for path in group}
        self.assertEqual({self.original, reencoded, brighter}, matched)

    def test_scan_order_and_groups_are_deterministic(self):
        copy = os.path.join(self.test_dir, "A-copy.png")
        shutil.copy2(self.original, copy)
        scanner = ImageScanner()
        first = scanner.scan_directory(self.test_dir, similarity=100)
        second = scanner.scan_directory(self.test_dir, similarity=100)
        self.assertEqual(first, second)

    def test_corrupt_image_is_reported_as_skipped(self):
        corrupt = os.path.join(self.test_dir, "broken.jpg")
        with open(corrupt, "wb") as output:
            output.write(b"not an image")
        scanner = ImageScanner()
        scanner.scan_directory(self.test_dir, similarity=85)
        self.assertEqual(corrupt, scanner.skipped_files[0][0])

    def test_cancellation(self):
        with self.assertRaises(ScanCancelled):
            ImageScanner().scan_directory(self.test_dir, cancel_check=lambda: True)

    def test_discovery_reports_images_in_subfolders(self):
        nested = os.path.join(self.test_dir, "album", "trip")
        os.makedirs(nested)
        shutil.copy2(self.original, os.path.join(nested, "nested.png"))
        updates = []
        ImageScanner().scan_directory(
            self.test_dir,
            similarity=100,
            discovery_callback=lambda count, folder: updates.append((count, folder)),
        )
        self.assertEqual(2, updates[-1][0])
        self.assertTrue(any(folder.endswith(os.path.join("album", "trip")) for _, folder in updates))

    def test_keeper_quality_prefers_higher_resolution(self):
        larger = os.path.join(self.test_dir, "larger.png")
        Image.new("RGB", (500, 500), "black").save(larger)
        self.assertGreater(get_image_quality(larger), get_image_quality(self.original))

    def test_format_size(self):
        self.assertEqual(format_size(100), "100.00 B")
        self.assertEqual(format_size(1024), "1.00 KB")
        self.assertEqual(format_size(1024 * 1024), "1.00 MB")


if __name__ == "__main__":
    unittest.main()
