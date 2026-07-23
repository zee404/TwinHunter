"""Create presentation-ready variants from downloaded CC0 demo originals."""

import shutil
from pathlib import Path

from PIL import Image, ImageEnhance


ROOT = Path(__file__).resolve().parents[1] / "demo_dataset"
ORIGINALS = ROOT / "01 Originals"


def main():
    destinations = {
        "exact": ROOT / "02 Exact Copies",
        "resized": ROOT / "03 Resized Versions",
        "edited": ROOT / "04 Lightly Edited",
    }
    for folder in destinations.values():
        folder.mkdir(parents=True, exist_ok=True)

    originals = sorted(ORIGINALS.glob("*.jpg"))
    if not originals:
        raise SystemExit("No JPG originals found in demo_dataset/01 Originals")

    for source in originals:
        shutil.copy2(source, destinations["exact"] / f"{source.stem}_COPY.jpg")

        with Image.open(source) as image:
            normalized = image.convert("RGB")
            resized = normalized.copy()
            resized.thumbnail((960, 960), Image.Resampling.LANCZOS)
            resized.save(
                destinations["resized"] / f"{source.stem}_resized_960.jpg",
                quality=82,
                optimize=True,
            )

            edited = ImageEnhance.Color(normalized).enhance(1.12)
            edited = ImageEnhance.Brightness(edited).enhance(1.06)
            edited.save(
                destinations["edited"] / f"{source.stem}_warmer.jpg",
                quality=88,
                optimize=True,
            )

    print(f"Created {len(originals) * 3} variants from {len(originals)} originals in {ROOT}")


if __name__ == "__main__":
    main()
