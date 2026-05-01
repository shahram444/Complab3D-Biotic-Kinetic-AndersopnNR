# CompLaB3D — JOSS Submission Checklist

**Repository:** https://github.com/shahram444/Complab3D-Biotic-Kinetic-AndersopnNR  
**Target journal:** Journal of Open Source Software (JOSS)  
**Prepared:** 2026-04-29

---

## ✅ DONE — Files and Folders in This JOSS_Submit Snapshot

| Item | File/Folder | Status |
|------|------------|--------|
| JOSS paper | `paper/paper.md` | ✅ Complete — all required sections present |
| Bibliography | `paper/paper.bib` | ✅ Present |
| Figure 1 (solver flowchart) | `paper/figure1.png` | ✅ Present |
| Figure 2 (GUI flowchart) | `paper/figure2.png` | ✅ Present |
| OSI-approved root LICENSE | `LICENSE` | ✅ GNU AGPL v3 (full text) |
| GUI license | `GUI/LICENSE` | ✅ UGA Research Foundation copyright |
| Comprehensive README | `README.md` | ✅ 13 sections, 745 lines |
| Machine-readable citation | `CITATION.cff` | ✅ AGPL-3.0, authors with ORCIDs |
| Software metadata | `codemeta.json` | ✅ Present |
| Contribution guidelines | `CONTRIBUTING.md` | ✅ Present |
| Code of conduct | `CODE_OF_CONDUCT.md` | ✅ Present (Contributor Covenant) |
| Testing guide | `TESTING.md` | ✅ 553+ test details |
| Solver source | `src/` | ✅ Full C++ solver |
| GUI source (new v2.1) | `GUI/src/` | ✅ Active version |
| GUI launch script | `GUI/main.py` | ✅ Present |
| GUI packaging | `GUI/pyproject.toml`, `requirements*.txt` | ✅ Present |
| C++ unit tests | `tests/cpp/` | ✅ 256 GoogleTest tests |
| Analytical validation | `test_cases/abiotic/` | ✅ 5 validation cases |
| Python GUI tests | `GUI/tests/` | ✅ 297+ pytest tests |
| CI — C++ tests | `.github/workflows/cpp-tests.yml` | ✅ Present |
| CI — GUI tests | `.github/workflows/gui-tests.yml` | ✅ Present |
| CI — JOSS PDF bot | `.github/workflows/draft-pdf.yml` | ✅ Present |
| Documentation | `docs/` | ✅ User tutorial, technical guide, geometry guide |
| XML templates | `CompLaB.xml`, `CompLaB_planktonic.xml` | ✅ Present |
| Kinetics headers | `defineKinetics.hh`, `defineAbioticKinetics.hh` | ✅ Present |

---

## ⚠️ MANUAL CLEANUP REQUIRED (PowerShell — run as Administrator)

The `GUI/` folder in this snapshot contains **both** the old GUI version (`GUI/gui/`)
and the active new version (`GUI/src/`). Run these commands to clean up:

```powershell
# Remove old GUI version from JOSS_Submit
Remove-Item -Recurse -Force "C:\Users\shahr\OneDrive\Desktop\Shahram Files\Github-mirror\Complab3D-Biotic-Kinetic-AndersopnNR\JOSS_Submit\GUI\gui"

# Remove build artifacts (not needed for submission)
Remove-Item -Recurse -Force "C:\Users\shahr\OneDrive\Desktop\Shahram Files\Github-mirror\Complab3D-Biotic-Kinetic-AndersopnNR\JOSS_Submit\GUI\Webpages" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "C:\Users\shahr\OneDrive\Desktop\Shahram Files\Github-mirror\Complab3D-Biotic-Kinetic-AndersopnNR\JOSS_Submit\GUI\bin" -ErrorAction SilentlyContinue

# Also remove old GUI from main repo (if not done yet)
Remove-Item -Recurse -Force "C:\Users\shahr\OneDrive\Desktop\Shahram Files\Github-mirror\Complab3D-Biotic-Kinetic-AndersopnNR\GUI\gui" -ErrorAction SilentlyContinue
```

---

## ⏳ BEFORE SUBMITTING TO JOSS

### 1. Push everything to GitHub
```bash
cd "C:\Users\shahr\OneDrive\Desktop\Shahram Files\Github-mirror\Complab3D-Biotic-Kinetic-AndersopnNR"
git add -A
git commit -m "Prepare for JOSS submission: README, LICENSE, workflows, GUI cleanup"
git push origin main
```

### 2. Create a tagged release
JOSS requires a versioned release (not just a main branch commit):
```bash
git tag v2.1.0
git push origin v2.1.0
```

### 3. Wait for CI to pass
After pushing, check that all three GitHub Actions workflows pass:
- C++ Tests (cpp-tests.yml)
- GUI Tests (gui-tests.yml)
- Draft PDF (draft-pdf.yml) — download the PDF artifact and verify it looks correct

### 4. ⚠️ IMPORTANT: Wait for 6-month public repository history
JOSS requires the repository to have been **publicly available for at least 6 months**.
- Repository made public: **~February 5, 2026**
- Earliest JOSS submission date: **~August 5, 2026**

### 5. Submit at https://joss.theoj.org/papers/new
Fill in:
- Repository URL: `https://github.com/shahram444/Complab3D-Biotic-Kinetic-AndersopnNR`
- Branch/tag: `v2.1.0`
- Journal: JOSS
- Paper path: `paper/paper.md`

---

## 📋 JOSS Review Checklist (for editors)

### Software license
- Solver (`src/`): GNU Affero General Public License v3.0 — `LICENSE`
- GUI (`GUI/`): UGA Research Foundation proprietary — `GUI/LICENSE`
- Upstream dependency (Palabos): AGPL-3.0 (compatible with solver license)

### Automated tests
- 256 C++ unit tests via GoogleTest (`tests/cpp/`) — run without Palabos
- 297+ Python/GUI tests via pytest (`GUI/tests/`)
- 5 analytical validation cases (`test_cases/abiotic/`)
- All tests run on GitHub Actions CI (see badges in README)

### Verifying tests quickly (reviewers)
```bash
# C++ tests (~20 sec, no Palabos required):
cd tests/cpp && mkdir -p build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release && cmake --build . --parallel
ctest --output-on-failure

# GUI tests (~30 sec):
cd GUI && pip install -e ".[dev]"
QT_QPA_PLATFORM=offscreen python -m pytest tests/ -v --tb=short

# Validation dry-run (no solver compile needed):
python tests/run_validation.py --dry-run
```

### Paper sections present
- [x] Summary
- [x] Statement of Need
- [x] Model Description
- [x] State of the Field
- [x] Research Impact
- [x] AI Usage Disclosure
- [x] References / Bibliography

### Documentation
- [x] Installation instructions (README §3)
- [x] Running without GUI (README §4)
- [x] Running with GUI (README §5)
- [x] XML configuration reference (README §6 + docs/)
- [x] Full test guide (README §7 + TESTING.md)
- [x] API / kinetics documentation (annotated .hh headers)
- [x] Community guidelines (CONTRIBUTING.md, CODE_OF_CONDUCT.md)

---

## 📝 PAPER.MD — Required Sections Status

| Section | Status | Notes |
|---------|--------|-------|
| Summary | ✅ | Lines 26–30 |
| Statement of Need | ✅ | Lines 32–34 |
| Model Description | ✅ | Lines 36–96 (full physics) |
| State of the Field | ✅ | Lines 98–100 |
| Research Impact | ✅ | Lines 102–104 |
| AI Usage Disclosure | ✅ | Lines 106–108 |
| Figures | ✅ | figure1.png, figure2.png |
| References | ✅ | paper.bib |

---

*This checklist was generated on 2026-04-29 during JOSS submission preparation.*
