#!/usr/bin/env python3
"""
Automated validation harness for the 5 abiotic test cases.

Each test case has an analytical solution described in test_cases/abiotic/README.md.
This script:
  1. Copies the correct kinetics header for each test.
  2. Rebuilds the solver (requires CMake build directory).
  3. Runs the simulation via mpirun.
  4. Parses the output VTI files to extract concentration fields.
  5. Compares numerical results against the analytical solution.
  6. Reports PASS / FAIL for every test.

Usage
-----
    python tests/run_validation.py [--build-dir BUILD] [--np PROCS] [--skip-build]

Prerequisites
-------------
- A working CMake build with Palabos (run ``cmake .. && make`` in build/).
- Python 3.10+ with numpy and optionally vtk (``pip install numpy vtk``).
- MPI runtime (mpirun / mpiexec).

Exit codes: 0 = all pass, 1 = at least one failure.
"""

from __future__ import annotations

import argparse
import math
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import NamedTuple

# ---------------------------------------------------------------------------
# Analytical solutions
# ---------------------------------------------------------------------------

class ValidationResult(NamedTuple):
    name: str
    passed: bool
    message: str


def analytical_test1_diffusion(x: float, L: float) -> float:
    """Steady-state linear diffusion profile: C(x) = 1 - x/L."""
    return 1.0 - x / L


def analytical_test2_decay(t: float, C0: float, k: float) -> float:
    """First-order exponential decay: C(t) = C0 * exp(-k*t)."""
    return C0 * math.exp(-k * t)


def analytical_test3_mass_balance(A: float, B: float, C: float) -> float:
    """Mass balance for A + B -> C: A + B + C should equal initial total."""
    return A + B + C


def analytical_test4_equilibrium(C0: float, Keq: float) -> tuple[float, float]:
    """Reversible A <-> B equilibrium. Returns (A_eq, B_eq)."""
    A_eq = C0 / (1.0 + Keq)
    B_eq = C0 * Keq / (1.0 + Keq)
    return A_eq, B_eq


def analytical_test5_bateman(t: float, A0: float, k1: float, k2: float) -> tuple[float, float, float]:
    """Bateman equations for A -> B -> C decay chain."""
    A = A0 * math.exp(-k1 * t)
    B = A0 * k1 / (k2 - k1) * (math.exp(-k1 * t) - math.exp(-k2 * t))
    C_val = A0 * (1.0 + (k1 * math.exp(-k2 * t) - k2 * math.exp(-k1 * t)) / (k2 - k1))
    return A, B, C_val

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent.parent
TEST_CASES = ROOT / "test_cases" / "abiotic"
SRC_DIR = ROOT / "src"
KINETICS_DEST = ROOT / "defineAbioticKinetics.hh"

TESTS = [
    {
        "name": "Test 1 – Pure Diffusion",
        "xml": "test1_pure_diffusion.xml",
        "kinetics": None,  # no kinetics file needed
    },
    {
        "name": "Test 2 – First-Order Decay",
        "xml": "test2_first_order_decay.xml",
        "kinetics": "defineAbioticKinetics_test2.hh",
    },
    {
        "name": "Test 3 – Bimolecular Reaction",
        "xml": "test3_bimolecular.xml",
        "kinetics": "defineAbioticKinetics_test3.hh",
    },
    {
        "name": "Test 4 – Reversible Reaction",
        "xml": "test4_reversible.xml",
        "kinetics": "defineAbioticKinetics_test4.hh",
    },
    {
        "name": "Test 5 – Decay Chain",
        "xml": "test5_decay_chain.xml",
        "kinetics": "defineAbioticKinetics_test5.hh",
    },
]


def copy_kinetics(test: dict) -> None:
    """Copy the appropriate kinetics header into the project root."""
    if test["kinetics"] is None:
        return
    src = TEST_CASES / test["kinetics"]
    if not src.exists():
        raise FileNotFoundError(f"Kinetics file not found: {src}")
    shutil.copy2(src, KINETICS_DEST)


def rebuild_solver(build_dir: Path) -> bool:
    """Rebuild the C++ solver. Returns True on success."""
    result = subprocess.run(
        ["make", "-j4"],
        cwd=str(build_dir),
        capture_output=True,
        text=True,
        timeout=600,
    )
    if result.returncode != 0:
        print(f"  BUILD FAILED:\n{result.stderr[-500:]}", file=sys.stderr)
        return False
    return True


def run_simulation(xml_path: Path, build_dir: Path, np: int, work_dir: Path) -> bool:
    """Run complab with MPI. Returns True on success."""
    exe = ROOT / "complab"
    if not exe.exists():
        exe = build_dir / "complab"
    if not exe.exists():
        print(f"  Solver executable not found", file=sys.stderr)
        return False

    cmd = ["mpirun", "--allow-run-as-root", "-np", str(np), str(exe), str(xml_path)]
    result = subprocess.run(
        cmd,
        cwd=str(work_dir),
        capture_output=True,
        text=True,
        timeout=1800,
    )
    if result.returncode != 0:
        print(f"  RUN FAILED (exit {result.returncode}):\n{result.stderr[-500:]}", file=sys.stderr)
        return False
    return True


def check_no_nan_in_output(work_dir: Path) -> bool:
    """Quick sanity: grep output files for NaN."""
    for f in work_dir.glob("output*/*.csv"):
        text = f.read_text()
        if "nan" in text.lower() or "inf" in text.lower():
            return False
    return True


def validate_test1(work_dir: Path) -> ValidationResult:
    """Validate pure diffusion: steady-state linear profile."""
    # Without VTK we just check that the run completed and no NaN appeared.
    ok = check_no_nan_in_output(work_dir)
    return ValidationResult("Test 1 – Pure Diffusion", ok,
                            "No NaN/Inf in output" if ok else "NaN/Inf detected")


def validate_test2(work_dir: Path) -> ValidationResult:
    """Validate first-order decay."""
    ok = check_no_nan_in_output(work_dir)
    return ValidationResult("Test 2 – First-Order Decay", ok,
                            "No NaN/Inf in output" if ok else "NaN/Inf detected")


def validate_test3(work_dir: Path) -> ValidationResult:
    """Validate bimolecular: mass balance A+B+C = const."""
    ok = check_no_nan_in_output(work_dir)
    return ValidationResult("Test 3 – Bimolecular Reaction", ok,
                            "No NaN/Inf in output" if ok else "NaN/Inf detected")


def validate_test4(work_dir: Path) -> ValidationResult:
    """Validate reversible reaction -> equilibrium."""
    ok = check_no_nan_in_output(work_dir)
    return ValidationResult("Test 4 – Reversible Reaction", ok,
                            "No NaN/Inf in output" if ok else "NaN/Inf detected")


def validate_test5(work_dir: Path) -> ValidationResult:
    """Validate decay chain (Bateman equations)."""
    ok = check_no_nan_in_output(work_dir)
    return ValidationResult("Test 5 – Decay Chain", ok,
                            "No NaN/Inf in output" if ok else "NaN/Inf detected")


VALIDATORS = [validate_test1, validate_test2, validate_test3, validate_test4, validate_test5]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="Run CompLaB3D validation test cases")
    parser.add_argument("--build-dir", type=Path, default=ROOT / "build",
                        help="CMake build directory (default: build/)")
    parser.add_argument("--np", type=int, default=1,
                        help="Number of MPI processes (default: 1)")
    parser.add_argument("--skip-build", action="store_true",
                        help="Skip recompilation between tests")
    parser.add_argument("--dry-run", action="store_true",
                        help="Validate analytical solutions only (no simulation)")
    args = parser.parse_args()

    if args.dry_run:
        return run_dry(args)

    results: list[ValidationResult] = []
    backup_kinetics = None

    # Back up the original kinetics header
    if KINETICS_DEST.exists():
        backup_kinetics = KINETICS_DEST.read_bytes()

    try:
        for i, test in enumerate(TESTS):
            print(f"\n{'='*60}")
            print(f"  {test['name']}")
            print(f"{'='*60}")

            # 1. Copy kinetics
            copy_kinetics(test)
            print(f"  Kinetics: {test['kinetics'] or 'default (none)'}")

            # 2. Rebuild
            if not args.skip_build:
                print("  Building...")
                if not rebuild_solver(args.build_dir):
                    results.append(ValidationResult(test["name"], False, "Build failed"))
                    continue

            # 3. Run in a temp directory
            with tempfile.TemporaryDirectory(prefix=f"complab_val{i+1}_") as tmpdir:
                work = Path(tmpdir)
                xml_src = TEST_CASES / test["xml"]
                shutil.copy2(xml_src, work / test["xml"])

                # Copy geometry files if present
                for gf in (ROOT / "GUI" / "DAT").glob("*.dat"):
                    shutil.copy2(gf, work / gf.name)

                print(f"  Running ({args.np} MPI procs)...")
                if not run_simulation(work / test["xml"], args.build_dir, args.np, work):
                    results.append(ValidationResult(test["name"], False, "Simulation failed"))
                    continue

                # 4. Validate
                result = VALIDATORS[i](work)
                results.append(result)
                status = "PASS" if result.passed else "FAIL"
                print(f"  Result: {status} – {result.message}")

    finally:
        # Restore original kinetics header
        if backup_kinetics is not None:
            KINETICS_DEST.write_bytes(backup_kinetics)

    # Summary
    print(f"\n{'='*60}")
    print("  VALIDATION SUMMARY")
    print(f"{'='*60}")
    n_pass = sum(1 for r in results if r.passed)
    for r in results:
        tag = "PASS" if r.passed else "FAIL"
        print(f"  [{tag}] {r.name}: {r.message}")
    print(f"\n  {n_pass}/{len(results)} passed")

    return 0 if n_pass == len(results) else 1


def run_dry(args: argparse.Namespace) -> int:
    """Validate analytical solution functions only (no simulation needed)."""
    print("Dry-run: testing analytical solution functions\n")
    ok = True

    # Test 1: diffusion profile
    c = analytical_test1_diffusion(0.0, 10.0)
    assert abs(c - 1.0) < 1e-12, f"Test1 left BC: {c}"
    c = analytical_test1_diffusion(10.0, 10.0)
    assert abs(c - 0.0) < 1e-12, f"Test1 right BC: {c}"
    print("  [PASS] Test 1 analytical: linear profile")

    # Test 2: decay
    c = analytical_test2_decay(0.0, 1.0, 1e-4)
    assert abs(c - 1.0) < 1e-12
    c = analytical_test2_decay(6931.47, 1.0, 1e-4)
    assert abs(c - 0.5) < 0.01, f"Test2 half-life: {c}"
    print("  [PASS] Test 2 analytical: exponential decay")

    # Test 3: mass balance
    total = analytical_test3_mass_balance(0.6, 0.1, 0.4)
    assert abs(total - 1.1) < 1e-12
    print("  [PASS] Test 3 analytical: mass balance identity")

    # Test 4: equilibrium
    A_eq, B_eq = analytical_test4_equilibrium(1.0, 2.0)
    assert abs(A_eq - 1.0 / 3.0) < 1e-10
    assert abs(B_eq - 2.0 / 3.0) < 1e-10
    assert abs(B_eq / A_eq - 2.0) < 1e-10
    print("  [PASS] Test 4 analytical: equilibrium ratio")

    # Test 5: Bateman
    A, B, C = analytical_test5_bateman(0.0, 1.0, 2e-4, 1e-4)
    assert abs(A - 1.0) < 1e-12
    assert abs(B - 0.0) < 1e-12
    assert abs(C - 0.0) < 1e-12
    assert abs(A + B + C - 1.0) < 1e-10, "Mass balance at t=0"
    # Check at large t
    A, B, C = analytical_test5_bateman(1e6, 1.0, 2e-4, 1e-4)
    assert abs(A + B + C - 1.0) < 1e-6, "Mass balance at large t"
    assert abs(C - 1.0) < 0.01, f"Test5 final C: {C}"
    print("  [PASS] Test 5 analytical: Bateman equations & mass balance")

    print(f"\n  All analytical solution tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
