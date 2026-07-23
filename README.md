# TwinHunter

TwinHunter is a modern Windows desktop application for finding byte-identical and visually similar images. It helps review resized, recompressed, color-adjusted, and duplicate photos while keeping deletion decisions explicit and recoverable.

## Highlights

- Exact duplicate detection using SHA-256
- Visual similarity detection using perceptual, wavelet, and color hashes
- Recursive scanning across nested folders
- Discovery progress, analyzed-image count, elapsed time, and ETA
- Large hover previews and detailed image metadata
- Explicit keeper selection for every match group
- Highest-resolution image selected as the default keeper
- Files moved to the Windows Recycle Bin instead of permanently deleted
- Dark and light modern interfaces
- Scan cancellation and unreadable-file reporting

## How matching works

The similarity control ranges from 70% to 100%:

- **100%** uses SHA-256 and returns only byte-identical files.
- **85%** is the recommended visual-matching level for resized, recompressed, or lightly edited photos.
- **75–80%** performs broader scene matching and may include more false positives.

Visual matching combines structural perceptual hashes, wavelet hashes, and color-distribution hashes. Similarity scanning compares image pairs and can take longer on very large libraries.

> Always review every group before deletion. Similar-looking images are not guaranteed to be interchangeable.

## Install from source

Requirements:

- Windows 10 or Windows 11
- Python 3.11 or newer

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python main.py
```

Using the virtual environment's Python executable directly avoids changing the PowerShell execution policy.

## Build the Windows executable

Install development dependencies:

```powershell
.\.venv\Scripts\python -m pip install -r requirements-dev.txt
```

Then build:

```powershell
.\build_windows.ps1
```

The portable application is created at `dist\TwinHunter.exe`. Windows may display an unknown-publisher warning until release binaries are digitally signed.

## Create the presentation dataset

The repository includes a script that downloads three CC0 Wikimedia Commons photographs and creates exact copies, resized/recompressed variants, and lightly adjusted variants:

```powershell
.\scripts\prepare_demo_dataset.ps1
```

Scan the generated `demo_dataset` directory:

- At 100%, it produces three exact-copy groups.
- At 85%, it produces three visual groups containing four versions each.

The downloaded demo media is intentionally ignored by Git. Source and licensing links are documented by the preparation script and Wikimedia Commons file pages.

## Run tests

```powershell
.\.venv\Scripts\python -m unittest discover -s tests -v
```

## Safety

- TwinHunter never automatically deletes a detected image.
- Every result group retains an explicit keeper.
- The selected keeper cannot be marked for deletion.
- Confirmed files are moved to the Recycle Bin.
- Failed file operations leave the affected files unchanged and are reported.

## Supported formats

JPEG, PNG, BMP, GIF, TIFF, and WebP.

## Known limitations

- Visual similarity is probabilistic and requires user review.
- Pairwise visual comparison can be slow for very large collections.
- Animated images are compared using their first frame.
- Network and external drives may produce less stable ETA estimates.

## License

TwinHunter is available under the [MIT License](LICENSE).
