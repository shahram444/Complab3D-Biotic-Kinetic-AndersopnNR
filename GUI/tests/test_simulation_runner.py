"""Integration tests for the SimulationRunner / RunPanel / MainWindow
subprocess lifecycle.

These tests use **pytest-qt** and a small Python helper script that
mimics the C++ solver output so we can exercise every signal path,
buffer boundary, and cancellation scenario without needing the real
``complab`` binary.

Run with:
    cd GUI
    COMPLAB_DEBUG=1 python -m pytest tests/test_simulation_runner.py -v -s

Each test is annotated with the specific "subprocess killer" it targets.
"""

import gc
import os
import sys
import stat
import time
import textwrap
import logging
import subprocess
from pathlib import Path

import pytest

from PySide6.QtCore import QTimer, Qt, QThread, Signal, QCoreApplication
from PySide6.QtWidgets import QApplication

# ---------------------------------------------------------------------------
# Ensure the GUI package is importable
# ---------------------------------------------------------------------------
GUI_DIR = Path(__file__).resolve().parent.parent          # GUI/
SRC_DIR = GUI_DIR / "src"
sys.path.insert(0, str(GUI_DIR))

from src.core.simulation_runner import SimulationRunner   # noqa: E402

log = logging.getLogger("complab.test")

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def _setup_logging():
    """Mirror the production logging so test output is visible."""
    root = logging.getLogger("complab")
    if not root.handlers:
        root.setLevel(logging.DEBUG)
        h = logging.StreamHandler(sys.stderr)
        h.setLevel(logging.DEBUG)
        h.setFormatter(logging.Formatter(
            "%(asctime)s.%(msecs)03d [%(levelname)s] %(name)s: %(message)s",
            datefmt="%H:%M:%S"))
        root.addHandler(h)


@pytest.fixture()
def work_dir(tmp_path, _setup_logging):
    """Create a minimal working directory with a dummy CompLaB.xml and a
    fake ``complab`` executable (a Python script).
    """
    # Minimal XML so the runner doesn't bail out on missing file
    xml = tmp_path / "CompLaB.xml"
    xml.write_text("<CompLaB></CompLaB>")
    return tmp_path


def _write_fake_solver(tmp_path: Path, script_body: str) -> str:
    """Write a Python helper script that acts as a fake C++ solver.

    Returns the path to the executable script.
    Uses the current sys.executable for the shebang so it works in any
    Python environment.
    """
    exe = tmp_path / "complab"
    python = sys.executable  # e.g. /usr/local/bin/python3
    # Build the script without textwrap.dedent to avoid shebang corruption
    lines = [
        f"#!{python}",
        "import sys, time",
        textwrap.dedent(script_body),
    ]
    exe.write_text("\n".join(lines))
    exe.chmod(exe.stat().st_mode | stat.S_IEXEC)
    return str(exe)


# ---------------------------------------------------------------------------
# Helper: collect signals
# ---------------------------------------------------------------------------

class SignalCollector:
    """Accumulates emissions from SimulationRunner signals."""

    def __init__(self):
        self.lines: list[str] = []
        self.progress_events: list[tuple[int, int]] = []
        self.finished: list[tuple[int, str]] = []
        self.diagnostics: list[str] = []

    def on_line(self, text: str):
        self.lines.append(text)

    def on_progress(self, cur: int, mx: int):
        self.progress_events.append((cur, mx))

    def on_finished(self, code: int, msg: str):
        self.finished.append((code, msg))

    def on_diagnostic(self, text: str):
        self.diagnostics.append(text)

    def connect(self, runner: SimulationRunner):
        runner.output_line.connect(self.on_line)
        runner.progress.connect(self.on_progress)
        runner.finished_signal.connect(self.on_finished)
        runner.diagnostic_report.connect(self.on_diagnostic)


# ===================================================================
# TEST 1 – Normal completion (baseline sanity check)
# ===================================================================

class TestNormalCompletion:
    """Verify the happy path: solver runs, emits output, exits 0."""

    def test_normal_run(self, qtbot, work_dir):
        script = """\
print("ade_max_iT = 5")
for i in range(1, 6):
    print(f"iT = {i}")
    sys.stdout.flush()
print("Completed successfully")
"""
        exe = _write_fake_solver(work_dir, script)
        collector = SignalCollector()

        runner = SimulationRunner(exe, str(work_dir))
        collector.connect(runner)

        with qtbot.waitSignal(runner.finished_signal, timeout=15_000):
            runner.start()

        assert len(collector.finished) == 1
        rc, msg = collector.finished[0]
        assert rc == 0, f"Expected exit 0, got {rc}: {msg}"
        assert "successfully" in msg.lower()

        # Progress signals should have been emitted
        assert len(collector.progress_events) >= 5
        # Check last progress
        last_cur, last_max = collector.progress_events[-1]
        assert last_cur == 5
        assert last_max == 5


# ===================================================================
# TEST 2 – stdout/stderr buffer overflow
#   Killer: If the reader can't keep up, the child blocks on write()
#           and the GUI may think it's hung and kill it.
# ===================================================================

class TestBufferOverflow:
    """Simulate a solver that floods stdout with large output."""

    def test_high_volume_output(self, qtbot, work_dir):
        """5000 lines of output at full speed should not kill the process."""
        script = """\
print("ade_max_iT = 5000")
for i in range(1, 5001):
    print(f"iT = {i}  some extra data residual=1.23e-4 padding" + "x" * 200)
    sys.stdout.flush()
print("Done")
"""
        exe = _write_fake_solver(work_dir, script)
        collector = SignalCollector()

        runner = SimulationRunner(exe, str(work_dir))
        collector.connect(runner)

        with qtbot.waitSignal(runner.finished_signal, timeout=60_000):
            runner.start()

        rc, msg = collector.finished[0]
        assert rc == 0, (
            f"Buffer overflow: process died with rc={rc}.\n"
            f"Lines received: {len(collector.lines)}\n"
            f"Last 5 lines: {collector.lines[-5:]}"
        )

    def test_no_newline_partial_lines(self, qtbot, work_dir):
        """Output without trailing newline should still be read
        (only on process exit when the pipe closes)."""
        script = """\
import sys
sys.stdout.write("partial line no newline")
sys.stdout.flush()
"""
        exe = _write_fake_solver(work_dir, script)
        collector = SignalCollector()

        runner = SimulationRunner(exe, str(work_dir))
        collector.connect(runner)

        with qtbot.waitSignal(runner.finished_signal, timeout=10_000):
            runner.start()

        rc, _ = collector.finished[0]
        assert rc == 0


# ===================================================================
# TEST 3 – QThread/QObject garbage collection
#   Killer: If Python's GC collects the SimulationRunner while the
#           QThread is still running, the subprocess is silently killed.
# ===================================================================

class TestGarbageCollection:
    """Ensure the runner is not collected while the thread is alive.

    FINDING: In the first test run (without a parent), deleting the local
    reference caused ``QThread: Destroyed while thread is still running``
    → Fatal abort.  This proves that the runner MUST be stored in a
    long-lived attribute (like ``self._runner`` on the main window).

    The fix in main_window.py now calls ``wait()`` + ``deleteLater()``
    before replacing the runner.  This test verifies the safe pattern.
    """

    def test_runner_with_parent_survives_gc(self, qtbot, work_dir):
        """Runner with a QObject parent is protected from GC."""
        from PySide6.QtCore import QObject

        script = """\
import time
print("ade_max_iT = 3")
for i in range(1, 4):
    time.sleep(0.3)
    print(f"iT = {i}")
    sys.stdout.flush()
"""
        exe = _write_fake_solver(work_dir, script)
        collector = SignalCollector()

        # Create a parent that outlives the test scope
        parent = QObject()

        runner = SimulationRunner(exe, str(work_dir), parent=parent)
        collector.connect(runner)

        finished_sig = runner.finished_signal

        with qtbot.waitSignal(finished_sig, timeout=15_000):
            runner.start()

            # Drop the local reference and force GC.
            # Because parent keeps a C++ reference, the thread survives.
            runner_id = id(runner)
            del runner
            gc.collect()
            log.info("GC forced after deleting local runner ref (id=%s)",
                     runner_id)

        assert len(collector.finished) == 1
        rc, _ = collector.finished[0]
        assert rc == 0, "Runner was GC'd despite having a parent"

        # Clean up
        parent.deleteLater()

    def test_runner_without_parent_is_dangerous(self, qtbot, work_dir):
        """Demonstrate that a parentless runner IS killed by GC.

        We don't actually trigger the fatal abort (that would crash the
        test suite).  Instead we verify the runner has no parent and
        document this as a known risk that main_window.py must guard
        against.
        """
        script = 'print("quick")'
        exe = _write_fake_solver(work_dir, script)

        runner = SimulationRunner(exe, str(work_dir))  # no parent!
        assert runner.parent() is None, (
            "Parentless runner: GC can destroy this while the thread runs. "
            "main_window.py MUST keep a strong reference."
        )


# ===================================================================
# TEST 4 – Cancel / terminate
#   Killer: cancel() only sends SIGTERM; MPI trees may not forward it.
#           The fix is the process-group kill added in Step 2.
# ===================================================================

class TestCancelTerminate:
    """Verify that cancel() actually stops the subprocess."""

    def test_cancel_during_run(self, qtbot, work_dir):
        script = """\
import time
print("ade_max_iT = 9999")
for i in range(1, 10000):
    time.sleep(0.05)
    print(f"iT = {i}")
    sys.stdout.flush()
"""
        exe = _write_fake_solver(work_dir, script)
        collector = SignalCollector()

        runner = SimulationRunner(exe, str(work_dir))
        collector.connect(runner)

        runner.start()

        # Wait until at least some progress, then cancel
        qtbot.waitUntil(
            lambda: len(collector.progress_events) >= 3,
            timeout=10_000,
        )

        runner.cancel()

        # Wait for finished
        with qtbot.waitSignal(runner.finished_signal, timeout=15_000):
            pass  # already running, just wait

        rc, msg = collector.finished[0]
        assert "cancelled" in msg.lower() or rc != 0
        # The subprocess must actually be dead
        assert runner._process.poll() is not None, (
            "Subprocess still alive after cancel()!"
        )

    def test_cancel_sigterm_ignored(self, qtbot, work_dir):
        """Solver that traps SIGTERM — we should escalate to SIGKILL."""
        script = """\
import signal, time
signal.signal(signal.SIGTERM, lambda *a: None)  # ignore SIGTERM
print("ade_max_iT = 9999")
for i in range(1, 10000):
    time.sleep(0.05)
    print(f"iT = {i}")
    sys.stdout.flush()
"""
        exe = _write_fake_solver(work_dir, script)
        collector = SignalCollector()

        runner = SimulationRunner(exe, str(work_dir))
        collector.connect(runner)

        runner.start()

        qtbot.waitUntil(
            lambda: len(collector.progress_events) >= 2,
            timeout=10_000,
        )

        runner.cancel()

        with qtbot.waitSignal(runner.finished_signal, timeout=20_000):
            pass

        assert runner._process.poll() is not None, (
            "Process survived both SIGTERM and SIGKILL!"
        )


# ===================================================================
# TEST 5 – Working directory / environment
#   Killer: Solver can't find CompLaB.xml because cwd is wrong.
# ===================================================================

class TestWorkingDirectory:
    """Verify the subprocess runs in the correct working directory."""

    def test_cwd_is_work_dir(self, qtbot, work_dir):
        """The fake solver prints its cwd; must match work_dir."""
        script = """\
import os
print(f"CWD={os.getcwd()}")
"""
        exe = _write_fake_solver(work_dir, script)
        collector = SignalCollector()

        runner = SimulationRunner(exe, str(work_dir))
        collector.connect(runner)

        with qtbot.waitSignal(runner.finished_signal, timeout=10_000):
            runner.start()

        cwd_lines = [l for l in collector.lines if l.startswith("CWD=")]
        assert len(cwd_lines) >= 1
        reported_cwd = cwd_lines[0].split("=", 1)[1]
        assert os.path.realpath(reported_cwd) == os.path.realpath(str(work_dir))

    def test_missing_xml_fails_gracefully(self, qtbot, tmp_path, _setup_logging):
        """No CompLaB.xml → runner should emit error, not crash."""
        # tmp_path without XML
        exe = _write_fake_solver(tmp_path, "print('should not run')")
        collector = SignalCollector()

        runner = SimulationRunner(exe, str(tmp_path))
        collector.connect(runner)

        # Remove the XML the work_dir fixture would create
        xml = tmp_path / "CompLaB.xml"
        if xml.exists():
            xml.unlink()

        with qtbot.waitSignal(runner.finished_signal, timeout=10_000):
            runner.start()

        rc, _ = collector.finished[0]
        assert rc == -1
        assert any("not found" in l.lower() for l in collector.lines)


# ===================================================================
# TEST 6 – Non-zero exit code handling
#   Killer: Improper handling of crash codes may silently swallow errors.
# ===================================================================

class TestExitCodes:
    """Verify exit code propagation and diagnostic triggering."""

    def test_nonzero_exit(self, qtbot, work_dir):
        script = """\
print("Something went wrong")
sys.exit(42)
"""
        exe = _write_fake_solver(work_dir, script)
        collector = SignalCollector()

        runner = SimulationRunner(exe, str(work_dir))
        collector.connect(runner)

        with qtbot.waitSignal(runner.finished_signal, timeout=10_000):
            runner.start()

        rc, msg = collector.finished[0]
        assert rc == 42, f"Expected rc=42, got {rc}"
        assert "42" in msg

    def test_segfault_exit_code(self, qtbot, work_dir):
        """Simulate segfault (exit -11 / signal 11)."""
        script = """\
import os, signal
os.kill(os.getpid(), signal.SIGSEGV)
"""
        exe = _write_fake_solver(work_dir, script)
        collector = SignalCollector()

        runner = SimulationRunner(exe, str(work_dir))
        collector.connect(runner)

        with qtbot.waitSignal(runner.finished_signal, timeout=10_000):
            runner.start()

        rc, _ = collector.finished[0]
        # On Linux, death by signal N gives rc = -N
        assert rc == -11 or rc == 139, f"Expected SIGSEGV code, got {rc}"


# ===================================================================
# TEST 7 – Race condition: rapid start/stop/start
#   Killer: Starting a new simulation before the old thread fully exits
#           can orphan the old subprocess.
# ===================================================================

class TestRaceConditions:
    """Start → cancel → start in rapid succession."""

    def test_rapid_restart(self, qtbot, work_dir):
        """Cancel a runner and immediately create a new one."""
        script = """\
import time
print("ade_max_iT = 999")
for i in range(1, 1000):
    time.sleep(0.05)
    print(f"iT = {i}")
    sys.stdout.flush()
"""
        exe = _write_fake_solver(work_dir, script)

        # First runner — start, get some progress, cancel
        c1 = SignalCollector()
        r1 = SimulationRunner(exe, str(work_dir))
        c1.connect(r1)
        r1.start()

        qtbot.waitUntil(
            lambda: len(c1.progress_events) >= 2,
            timeout=10_000,
        )
        r1.cancel()

        # Wait for the finished signal (non-blocking wait via qtbot)
        qtbot.waitUntil(
            lambda: len(c1.finished) >= 1,
            timeout=15_000,
        )

        # Verify first process is dead
        assert r1._process.poll() is not None

        # Second runner — should work fine after the first is cleaned up
        c2 = SignalCollector()
        r2 = SimulationRunner(exe, str(work_dir))
        c2.connect(r2)
        r2.start()

        qtbot.waitUntil(
            lambda: len(c2.progress_events) >= 2,
            timeout=10_000,
        )
        r2.cancel()

        qtbot.waitUntil(
            lambda: len(c2.finished) >= 1,
            timeout=15_000,
        )
        assert r2._process.poll() is not None


# ===================================================================
# TEST 8 – MPI command not found
#   Killer: FileNotFoundError from Popen when mpirun doesn't exist.
# ===================================================================

class TestMPIErrors:
    """MPI mode with bad command should fail gracefully."""

    def test_mpi_command_not_found(self, qtbot, work_dir):
        exe = _write_fake_solver(work_dir, "print('hi')")
        collector = SignalCollector()

        runner = SimulationRunner(
            exe, str(work_dir),
            mpi_enabled=True,
            mpi_nprocs=4,
            mpi_command="/nonexistent/mpirun",
        )
        collector.connect(runner)

        with qtbot.waitSignal(runner.finished_signal, timeout=10_000):
            runner.start()

        rc, _ = collector.finished[0]
        assert rc == -1
        assert any("not found" in l.lower() or "error" in l.lower()
                    for l in collector.lines)


# ===================================================================
# TEST 9 – Progress parsing accuracy
# ===================================================================

class TestProgressParsing:
    """Verify regex-based iteration parsing."""

    def test_iteration_parsing(self, qtbot, work_dir):
        script = """\
print("ade_max_iT = 100")
for i in [1, 10, 50, 100]:
    print(f"iT = {i}")
    sys.stdout.flush()
"""
        exe = _write_fake_solver(work_dir, script)
        collector = SignalCollector()

        runner = SimulationRunner(exe, str(work_dir))
        collector.connect(runner)

        with qtbot.waitSignal(runner.finished_signal, timeout=10_000):
            runner.start()

        # Check all expected iterations were parsed
        iters = [cur for cur, _ in collector.progress_events]
        assert 1 in iters
        assert 100 in iters
        # max should be 100
        maxes = [mx for _, mx in collector.progress_events]
        assert 100 in maxes


# ===================================================================
# TEST 10 – Long-running process with slow output
#   Killer: readline() blocks for long periods; if the event loop
#           doesn't process events the GUI freezes and the user may
#           force-quit, killing the subprocess.
# ===================================================================

class TestSlowOutput:
    """Solver that produces output infrequently."""

    def test_slow_output_survives(self, qtbot, work_dir):
        script = """\
import time
print("ade_max_iT = 3")
sys.stdout.flush()
for i in range(1, 4):
    time.sleep(1.0)
    print(f"iT = {i}")
    sys.stdout.flush()
print("Done")
"""
        exe = _write_fake_solver(work_dir, script)
        collector = SignalCollector()

        runner = SimulationRunner(exe, str(work_dir))
        collector.connect(runner)

        with qtbot.waitSignal(runner.finished_signal, timeout=30_000):
            runner.start()

        rc, _ = collector.finished[0]
        assert rc == 0, f"Slow output caused premature termination: rc={rc}"
        assert len(collector.progress_events) >= 3


# ===================================================================
# TEST 11 – Log file creation
# ===================================================================

class TestLogFile:
    """Verify that a log file is created in output/."""

    def test_log_file_written(self, qtbot, work_dir):
        script = """\
print("Hello from solver")
print("iT = 1")
sys.stdout.flush()
"""
        exe = _write_fake_solver(work_dir, script)
        collector = SignalCollector()

        runner = SimulationRunner(exe, str(work_dir))
        collector.connect(runner)

        with qtbot.waitSignal(runner.finished_signal, timeout=10_000):
            runner.start()

        # Check output/ dir for a .out file
        output_dir = work_dir / "output"
        assert output_dir.exists()
        out_files = list(output_dir.glob("simulation_*.out"))
        assert len(out_files) >= 1

        content = out_files[0].read_text()
        assert "Hello from solver" in content
