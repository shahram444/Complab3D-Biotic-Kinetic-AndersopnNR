"""
md_to_pdf.py
============
Converts a Markdown (.md) file to PDF using the EXACT same Docker command
we have been running manually in PowerShell:

  docker run --rm --entrypoint pandoc -v "${PWD}:/data" -w /data openjournals/inara  FILE.md  -o FILE.pdf  --pdf-engine=xelatex

This script just automates that command so you don't have to type it.
The .md file and all image files must be in the same folder.

Usage (run from any folder -- the script handles the cd automatically):
  python md_to_pdf.py  appendix_A.md
  python md_to_pdf.py  appendix_B.md  appendix_B.pdf   (custom output name)

Requirements:
  - Python 3.7+
  - Docker Desktop installed and running
"""

import subprocess   # to run shell commands from Python
import sys          # to read command-line arguments
import os           # for file/path operations


# ---------------------------------------------------------------------------
# STEP 0 - Read arguments
# ---------------------------------------------------------------------------

if len(sys.argv) < 2:
    print("Usage: python md_to_pdf.py  <input.md>  [output.pdf]")
    print("Example: python md_to_pdf.py  appendix_A.md")
    sys.exit(1)

md_input   = sys.argv[1]                                  # e.g. "appendix_A.md"
md_folder  = os.path.abspath(os.path.dirname(md_input))  # absolute path of the folder
md_file    = os.path.basename(md_input)                   # just the filename

# If md_input has no directory part (e.g. user typed just "appendix_A.md"),
# os.path.dirname returns "" -- fall back to the current working directory
if not md_folder or md_folder == '':
    md_folder = os.getcwd()

# Output PDF name: same as input but with .pdf extension (unless user supplied one)
if len(sys.argv) >= 3:
    pdf_file = sys.argv[2]
else:
    pdf_file = os.path.splitext(md_file)[0] + '.pdf'     # appendix_A.md --> appendix_A.pdf

print(f"Input  : {md_input}")
print(f"Output : {os.path.join(md_folder, pdf_file)}")
print()


# ---------------------------------------------------------------------------
# STEP 1 - Check Docker is running
# ---------------------------------------------------------------------------

print("Checking Docker ...")
check = subprocess.run(['docker', 'info'], capture_output=True)
if check.returncode != 0:
    print("ERROR: Docker is not running.")
    print("  Please start Docker Desktop and try again.")
    sys.exit(1)
print("  Docker OK")
print()


# ---------------------------------------------------------------------------
# STEP 2 - Build and run the exact same command we use in PowerShell
# ---------------------------------------------------------------------------
# The manual PowerShell command is:
#
#   cd "C:\path\to\folder"
#   docker run --rm --entrypoint pandoc -v "${PWD}:/data" -w /data openjournals/inara appendix_A.md -o appendix_A.pdf --pdf-engine=xelatex
#
# This script replaces ${PWD} with the actual folder path automatically.
# On Windows, Docker Desktop accepts the raw Windows path (e.g. C:\Users\...)
# when shell=True is used.

# Build the shell command as a plain string -- identical to what you type manually
cmd = (
    f'docker run --rm --entrypoint pandoc '
    f'-v "{md_folder}:/data" '
    f'-w /data '
    f'openjournals/inara '
    f'{md_file} '
    f'-o {pdf_file} '
    f'--pdf-engine=xelatex'
)

print("Running command:")
print(f"  {cmd}")
print()

# Execute the command.
# shell=True means Python passes it to the system shell (cmd.exe on Windows,
# bash on macOS/Linux) -- exactly as if you typed it yourself in the terminal.
result = subprocess.run(cmd, shell=True)


# ---------------------------------------------------------------------------
# STEP 3 - Report result
# ---------------------------------------------------------------------------

print()
if result.returncode == 0:
    output_path = os.path.join(md_folder, pdf_file)
    print(f"SUCCESS!  PDF written to:")
    print(f"  {output_path}")
else:
    print(f"ERROR: command failed with exit code {result.returncode}")
    print()
    print("Common fixes:")
    print("  'Missing character' warning  -->  replace the Unicode symbol in the .md file")
    print("      e.g.  x  -->  $\\times$     -  -->  $-$     >=  -->  $\\geq$     +-  -->  $\\pm$")
    print()
    print("  'File not found' error  -->  make sure the .md file AND all imageN.png files")
    print(f"     are in the same folder:  {md_folder}")
    print()
    print("  'fvextra.sty not found'  -->  remove \\usepackage{fvextra} from the YAML header")
    print("     at the top of the .md file and replace it with:")
    print(r"       - \makeatletter\def\verbatim@font{\footnotesize\ttfamily}\makeatother")
    sys.exit(1)
