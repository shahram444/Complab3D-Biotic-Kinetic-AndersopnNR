# CompLaB3D — JOSS Paper Submission Materials

This folder contains the source files for the JOSS paper *"CompLaB3D: A
Three-Dimensional Pore-Scale Reactive Transport Model Framework and
Graphical User Interface Coupling Lattice Boltzmann Flow with Biogeochemical
Kinetics, Equilibrium Chemistry and Biofilm Dynamics"* (Asgari & Meile,
University of Georgia) together with all supplementary appendices and the
exact commands needed to rebuild every PDF locally.

Everything below is self-contained: the only external dependency is
**Docker Desktop**.

---

## 1. Folder Structure

```
Paper Joss/
├── README.md                       <-- you are here
├── paper.md                        <-- JOSS paper source (Markdown + YAML)
├── paper.bib                       <-- BibTeX bibliography (13 entries)
├── paper-joss format-draft.pdf     <-- pre-built JOSS-formatted PDF of paper.md
├── Figure 1.jpg                    <-- Figure 1: simulation flowchart
├── Figure 2.jpg                    <-- Figure 2: GUI workflow flowchart
│
└── Appendices/
    │
    ├── appendix_A.md               <-- Appendix A source (Equilibrium Solver)
    ├── appendix_A.pdf              <-- pre-built PDF of Appendix A
    │
    ├── appendix_B.md               <-- Appendix B source (Biofilm CA Algorithm)
    ├── Appendix_B.pdf              <-- pre-built PDF of Appendix B
    │
    ├── appendix_C.md               <-- Appendix C source (CompLaB Studio GUI)
    ├── appendix_C.pdf              <-- pre-built PDF of Appendix C
    │
    ├── figA1.png ... figA5.png     <-- figures referenced by appendix_A.md
    ├── figB2.png ... figB7.png     <-- figures referenced by appendix_B.md
    └── imageC1.png ... imageC13.png <-- screenshots referenced by appendix_C.md
```

---

## 2. What Each File Is

### Main paper (top level)

| File                          | Purpose                                                                                                                                                |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `paper.md`                    | The JOSS paper. Markdown with a YAML frontmatter (title, authors, ORCIDs, affiliations, tags, bibliography reference). This is the file JOSS compiles. |
| `paper.bib`                   | Bibliography in BibTeX format. Every `@key` cited in `paper.md` resolves here.                                                                         |
| `Figure 1.jpg`                | Simulation flowchart referenced from `paper.md`. Detailed description in Appendix C §C.14.1.                                                           |
| `Figure 2.jpg`                | GUI workflow flowchart referenced from `paper.md`. Detailed description in Appendix C §C.14.2.                                                         |
| `paper-joss format-draft.pdf` | Pre-rendered JOSS-formatted PDF of `paper.md` (with JOSS logo, header, citation style). Built using the procedure in Section 3 below.                  |

### Appendices (subfolder)

| File                                    | Purpose                                                                                                                                                                                                                                                                                          |
| --------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `appendix_A.md` / `.pdf`                | **Equilibrium Solver.** Mathematical derivation of the Positive Continuous Fractions (PCF) method and Anderson Acceleration used by the equilibrium chemistry module, with a five-step PCF derivation (A1) and a four-step AA derivation (A2). Includes 5 explanatory figures (`figA1`–`figA5`). |
| `appendix_B.md` / `.pdf`                | **Biofilm Growth and Redistribution Algorithm.** Pseudocode for the cellular automaton (CA) that handles biomass redistribution: main CA loop (B.1), full-push (B.2), half-push (B.3), MPI boundary exchange (B.4), and voxel reclassification (B.5). Includes 6 figures (`figB2`–`figB7`).      |
| `appendix_C.md` / `.pdf`                | **CompLaB Studio GUI.** Walkthrough of the cross-platform PySide6 graphical interface, organized panel-by-panel (C.1–C.13) with a final flowchart explanation (C.14). Includes 13 GUI screenshots (`imageC1`–`imageC13`).                                                                        |
| `figA*.png`, `figB*.png`, `imageC*.png` | Figures referenced by their respective appendix Markdown files. They must remain in the same folder as the appendix `.md` when rebuilding.                                                                                                                                                       |

---

## 3. Rebuilding the PDFs from Source

All PDFs in this folder were built with **Docker** using the official JOSS
toolchain image **`openjournals/inara`**. You do not need to install LaTeX,
pandoc, or any Python packages — Docker pulls everything it needs.

### 3.1 Prerequisites

1. Install **Docker Desktop** (Windows/macOS) or the Docker engine (Linux).
   Download: <https://www.docker.com/products/docker-desktop/>

2. Start Docker Desktop and wait until it reports *"Docker is running."*

3. Verify from a terminal:
   
   ```bash
   docker info
   ```
   
   If this prints the daemon configuration without errors, you are ready.

The first PDF build will pull the `openjournals/inara` image
(roughly 2 GB, one-time download). Subsequent builds reuse the cached image
and finish in seconds.

### 3.2 Building the main paper (JOSS-formatted PDF)

The main paper uses the full **inara** entrypoint, which applies the
official JOSS layout: JOSS logo, author/affiliation block, JOSS citation
style, and DOI metadata.

From a terminal **inside the `Paper Joss/` folder**:

**Linux / macOS / Windows PowerShell:**

```bash
docker run --rm -v "${PWD}:/data" openjournals/inara -p pdf paper.md
```

**Windows Command Prompt (cmd.exe):**

```cmd
docker run --rm -v "%cd%:/data" openjournals/inara -p pdf paper.md
```

Output: `paper.pdf` is written next to `paper.md`. The pre-built copy in
this folder is named `paper-joss format-draft.pdf` to keep the source PDF
and rebuilt PDF distinguishable.

**Notes:**

- `paper.bib` must be in the same folder as `paper.md` (it already is).
- Every `@citationkey` in `paper.md` must exist in `paper.bib`.
- Figures (`Figure 1.jpg`, `Figure 2.jpg`) must be in the same folder.

### 3.3 Building the appendices (plain PDF)

The appendices are not JOSS articles, so they are rendered with a plain
**pandoc + xelatex** pass instead of the full inara wrapper. The same
Docker image is reused; only the entrypoint is overridden.

From a terminal **inside the `Appendices/` subfolder**:

**Linux / macOS / Windows PowerShell:**

```bash
docker run --rm --entrypoint pandoc -v "${PWD}:/data" -w /data \
  openjournals/inara appendix_A.md -o appendix_A.pdf --pdf-engine=xelatex

docker run --rm --entrypoint pandoc -v "${PWD}:/data" -w /data \
  openjournals/inara appendix_B.md -o appendix_B.pdf --pdf-engine=xelatex

docker run --rm --entrypoint pandoc -v "${PWD}:/data" -w /data \
  openjournals/inara appendix_C.md -o appendix_C.pdf --pdf-engine=xelatex
```

**Windows Command Prompt:**

```cmd
docker run --rm --entrypoint pandoc -v "%cd%:/data" -w /data openjournals/inara appendix_A.md -o appendix_A.pdf --pdf-engine=xelatex
docker run --rm --entrypoint pandoc -v "%cd%:/data" -w /data openjournals/inara appendix_B.md -o appendix_B.pdf --pdf-engine=xelatex
docker run --rm --entrypoint pandoc -v "%cd%:/data" -w /data openjournals/inara appendix_C.md -o appendix_C.pdf --pdf-engine=xelatex
```

Each command writes its respective `.pdf` next to the source `.md`.
All `figA*`, `figB*`, and `imageC*` PNGs must remain in this same folder
during the build.

### 3.4 What each command actually does

```
docker run                  start a fresh container
  --rm                      delete the container when finished
  -v "${PWD}:/data"         mount the current host folder as /data inside container
  -w /data                  set /data as the working directory
  --entrypoint pandoc       (appendices only) override default entrypoint
  openjournals/inara        the JOSS Docker image
  -p pdf paper.md           (main paper) inara flags: produce PDF from paper.md
  appendix_X.md ...         (appendices) pandoc input + flags
```

The main-paper command uses the image's default entrypoint (`inara`),
so it gets full JOSS styling. The appendix command overrides the
entrypoint to `pandoc`, producing a clean academic PDF without any
JOSS-specific decorations.

---

## 4. Troubleshooting

| Symptom                                    | Fix                                                                                                                                                                          |
| ------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Cannot connect to the Docker daemon`      | Start Docker Desktop and wait for it to finish initializing.                                                                                                                 |
| `paper.bib not found`                      | Confirm `paper.bib` is in the same folder as `paper.md`. The mount path must be that folder.                                                                                 |
| `Citation 'foo' not found`                 | The `@foo` key in `paper.md` is missing from `paper.bib`. Add the entry or fix the typo.                                                                                     |
| `File 'figX.png' not found`                | A figure referenced by an appendix is missing from the build folder. Make sure all `figA*`, `figB*`, `imageC*` PNGs are in `Appendices/` when running the appendix commands. |
| `Missing character` warning during xelatex | Replace the offending Unicode character in the `.md` source — e.g. `×` → `$\times$`, `–` → `$-$`, `≥` → `$\geq$`, `±` → `$\pm$`.                                             |
| Build is very slow on first run            | Docker is downloading `openjournals/inara` (~2 GB). One-time only; subsequent builds are fast.                                                                               |

---

## 5. Quick Reproducibility Check

To verify the toolchain end-to-end, the full sequence (from the
`Paper Joss/` folder, in PowerShell or bash) is:

```bash
# Main paper (JOSS-formatted)
docker run --rm -v "${PWD}:/data" openjournals/inara -p pdf paper.md

# Appendices (plain pandoc)
cd Appendices
docker run --rm --entrypoint pandoc -v "${PWD}:/data" -w /data openjournals/inara appendix_A.md -o appendix_A.pdf --pdf-engine=xelatex
docker run --rm --entrypoint pandoc -v "${PWD}:/data" -w /data openjournals/inara appendix_B.md -o appendix_B.pdf --pdf-engine=xelatex
docker run --rm --entrypoint pandoc -v "${PWD}:/data" -w /data openjournals/inara appendix_C.md -o appendix_C.pdf --pdf-engine=xelatex
cd ..
```

Compare the freshly-built PDFs with the pre-built copies provided in this
folder. They should be byte-identical (or differ only in build timestamps).

---

## 6. Citation

Asgari, S., & Meile, C. (2026). *CompLaB3D: A Three-Dimensional Pore-Scale
Reactive Transport Model Framework and Graphical User Interface Coupling
Lattice Boltzmann Flow with Biogeochemical Kinetics, Equilibrium Chemistry
and Biofilm Dynamics.* Journal of Open Source Software (in review).
