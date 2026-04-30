"""
joss_compile.py
===============
Compiles a JOSS paper.md to a full JOSS-formatted PDF using the official
openjournals/inara Docker image -- the exact same tool JOSS uses on their
editorial servers.

This produces a proper JOSS PDF with:
  - JOSS logo and header
  - Author names and affiliations block
  - JOSS citation style
  - DOI and repository metadata from the YAML frontmatter

Use this script for the main paper.md.
Use md_to_pdf.py for appendices (plain PDF, no JOSS formatting).

Usage:
  python joss_compile.py                    # compiles paper.md by default
  python joss_compile.py  paper.md          # same, explicit file name
  python joss_compile.py  paper.md  pdf     # PDF only (fastest)
  python joss_compile.py  paper.md  pdf,crossref  # PDF + crossref metadata

Requirements:
  - Python 3.7+
  - Docker Desktop installed and running
  - paper.md must have valid JOSS YAML frontmatter (title, authors, affiliations, bibliography)
  - paper.bib must be in the same folder as paper.md
"""

import subprocess   # to run shell commands from Python
import sys          # to read command-line arguments
import os           # for file/path operations


# ---------------------------------------------------------------------------
# STEP 0 - Read arguments
# ---------------------------------------------------------------------------

# Default: compile paper.md with pdf output
md_input        = sys.argv[1] if len(sys.argv) >= 2 else 'paper.md'
output_formats  = sys.argv[2] if len(sys.argv) >= 3 else 'pdf'

md_folder = os.path.abspath(os.path.dirname(md_input))
md_file   = os.path.basename(md_input)

# If no directory part in md_input, use current working directory
if not md_folder or md_folder == '':
    md_folder = os.getcwd()

print(f"Paper  : {md_input}")
print(f"Folder : {md_folder}")
print(f"Output : {output_formats}")
print()


# ---------------------------------------------------------------------------
# STEP 1 - Check that paper.bib exists (inara requires it)
# ---------------------------------------------------------------------------

bib_path = os.path.join(md_folder, 'paper.bib')
if not os.path.exists(bib_path):
    print(f"WARNING: paper.bib not found in {md_folder}")
    print("  inara requires a paper.bib file even if you have no citations.")
    print("  Create an empty paper.bib file or copy your bibliography there.")
    print()


# ---------------------------------------------------------------------------
# STEP 2 - Check Docker is running
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
# STEP 3 - Build and run the inara command
# ---------------------------------------------------------------------------
# inara is JOSS's own paper compiler.
# The command format is:
#
#   docker run --rm -v "FOLDER:/data" openjournals/inara -p pdf paper.md
#
# Note: this is different from md_to_pdf.py which uses --entrypoint pandoc.
# Here we use inara directly (no --entrypoint override) so it applies
# all JOSS formatting, logo, and citation style.

cmd = (
    f'docker run --rm '
    f'-v "{md_folder}:/data" '
    f'openjournals/inara '
    f'-p {output_formats} '
    f'{md_file}'
)

print("Running inara:")
print(f"  {cmd}")
print()

# shell=True passes the command string to the system shell exactly as typed
result = subprocess.run(cmd, shell=True)


# ---------------------------------------------------------------------------
# STEP 4 - Report result
# ---------------------------------------------------------------------------

print()
if result.returncode == 0:
    pdf_path = os.path.join(md_folder, os.path.splitext(md_file)[0] + '.pdf')
    print("SUCCESS!")
    print(f"  PDF written to: {pdf_path}")
else:
    print(f"ERROR: inara failed with exit code {result.returncode}")
    print()
    print("Common fixes:")
    print("  'Docker is not running'   -->  start Docker Desktop from the Start menu")
    print("  'paper.bib not found'     -->  make sure paper.bib is in the same folder as paper.md")
    print("  'YAML parse error'        -->  check your YAML frontmatter indentation")
    print("  'Citation not found'      -->  every @key in paper.md must be in paper.bib")
    print("  'Missing character'       -->  replace Unicode: x -> $\\times$  - -> $-$  >= -> $\\geq$")
    print("  'File not found'          -->  move the figure .png into the same folder as paper.md")
    sys.exit(1)
