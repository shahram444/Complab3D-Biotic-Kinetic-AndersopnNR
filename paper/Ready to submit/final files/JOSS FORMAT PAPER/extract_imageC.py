"""
extract_imageC.py
=================
One-time helper: extracts the 13 figures from Appendix_C-SA-submit.docx
and saves them as imageC1.png ... imageC13.png in this folder.

Run once from the JOSS FORMAT PAPER folder:
  python extract_imageC.py
"""

import zipfile, os, sys

# Path to the source docx (adjust if needed)
DOCX = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "Appendix_C-SA-submit.docx"
)
OUT_DIR = os.path.dirname(os.path.abspath(__file__))

if not os.path.exists(DOCX):
    print(f"ERROR: Cannot find {DOCX}")
    print("Move Appendix_C-SA-submit.docx next to this script's parent folder.")
    sys.exit(1)

counter = 0
with zipfile.ZipFile(DOCX) as z:
    media_files = sorted([f for f in z.namelist() if f.startswith('word/media/')])
    for entry in media_files:
        counter += 1
        ext = os.path.splitext(entry)[1] or '.png'
        out_name = f"imageC{counter}.png"
        data = z.read(entry)
        out_path = os.path.join(OUT_DIR, out_name)
        with open(out_path, 'wb') as f:
            f.write(data)
        print(f"  Extracted {out_name}  ({len(data)} bytes)")

print(f"\nDone. {counter} images extracted to {OUT_DIR}")
