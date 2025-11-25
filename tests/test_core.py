import unittest
import os
import shutil
from PIL import Image
from core.scanner import ImageScanner
from core.utils import format_size

class TestCore(unittest.TestCase):
    def setUp(self):
        self.test_dir = "test_images"
        os.makedirs(self.test_dir, exist_ok=True)
        
        # Create a base image (half black, half white)
        self.img1_path = os.path.join(self.test_dir, "img1.png")
        img = Image.new('L', (100, 100), color = 0)
        for x in range(50):
            for y in range(100):
                img.putpixel((x, y), 255)
        img.save(self.img1_path)
        
        # Create a duplicate
        self.img2_path = os.path.join(self.test_dir, "img2.png")
        shutil.copy(self.img1_path, self.img2_path)
        
        # Create a different image (all black)
        self.img3_path = os.path.join(self.test_dir, "img3.png")
        img2 = Image.new('L', (100, 100), color = 0)
        img2.save(self.img3_path)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_scanner(self):
        scanner = ImageScanner()
        duplicates = scanner.scan_directory(self.test_dir)
        
        # Should find one group of duplicates
        self.assertEqual(len(duplicates), 1)
        
        # The group should contain img1 and img2
        for hash_val, files in duplicates.items():
            self.assertEqual(len(files), 2)
            self.assertIn(self.img1_path, files)
            self.assertIn(self.img2_path, files)
            self.assertNotIn(self.img3_path, files)

    def test_format_size(self):
        self.assertEqual(format_size(100), "100.00 B")
        self.assertEqual(format_size(1024), "1.00 KB")
        self.assertEqual(format_size(1024 * 1024), "1.00 MB")

if __name__ == '__main__':
    unittest.main()
