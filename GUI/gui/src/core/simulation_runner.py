"""
Simulation Runner - Execute CompLaB simulations with detailed error handling
"""

import os
import re
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Tuple

from PySide6.QtCore import QThread, Signal, QProcess

from .project import CompLaBProject


class SimulationRunner(QThread):
    """Run CompLaB simulation in a separate thread with detailed error reporting"""
    
    # Signals
    started = Signal()
    finished = Signal(int)  # exit code
    progress = Signal(int, str)  # iteration, message
    output = Signal(str)  # console output
    error = Signal(str)  # error message
    
    def __init__(self, project: CompLaBProject, parent=None):
        super().__init__(parent)
        self.project = project
        self.process: Optional[QProcess] = None
        self._stop_requested = False
        self._log_file = None
        self._log_path = None
        self._output_buffer = []  # Store all output for error analysis
        self._last_error = ""
        
    def run(self):
        """Execute the simulation"""
        try:
            self.started.emit()
            self._output_buffer = []
            
            # === PRE-FLIGHT CHECKS ===
            self._log_and_emit("=" * 60)
            self._log_and_emit("CompLaB Pre-Flight Checks")
            self._log_and_emit("=" * 60)
            
            # Check 1: CompLaB executable
            complab_exe = self._find_complab_executable()
            if not complab_exe:
                self._emit_error(
                    "CompLaB executable not found",
                    "The complab.exe file could not be located.",
                    [
                        "Check that CompLaB is installed at:",
                        "  C:\\Users\\<username>\\AppData\\Local\\CompLaB_Studio\\bin\\complab.exe",
                        "Or set COMPLAB_PATH environment variable to the executable path."
                    ]
                )
                self.finished.emit(-1)
                return
            self._log_and_emit(f"✓ Executable: {complab_exe}")
            
            # Check 2: Project directory
            project_dir = self.project.get_project_dir()
            if not project_dir or not os.path.exists(project_dir):
                self._emit_error(
                    "Project directory not found",
                    f"Directory does not exist: {project_dir}",
                    ["Save the project first before running."]
                )
                self.finished.emit(-1)
                return
            self._log_and_emit(f"✓ Project directory: {project_dir}")
            
            # Check 3: Input directory
            input_dir = self.project.get_input_dir()
            if not os.path.exists(input_dir):
                self._emit_error(
                    "Input directory not found",
                    f"Directory does not exist: {input_dir}",
                    [
                        "Create the 'input' folder in your project directory.",
                        "Place your geometry .dat file in the input folder."
                    ]
                )
                self.finished.emit(-1)
                return
            self._log_and_emit(f"✓ Input directory: {input_dir}")
            
            # Check 4: Geometry file
            geom_file = self.project.domain.geometry_file
            if not geom_file:
                self._emit_error(
                    "No geometry file specified",
                    "The geometry file name is empty.",
                    [
                        "Go to Domain tab and specify a geometry file name.",
                        "Example: geometry.dat or FibHbase3D.dat"
                    ]
                )
                self.finished.emit(-1)
                return
                
            geom_path = os.path.join(input_dir, geom_file)
            if not os.path.exists(geom_path):
                self._emit_error(
                    "Geometry file not found",
                    f"File does not exist: {geom_path}",
                    [
                        f"Make sure '{geom_file}' exists in the input folder.",
                        "The file should be created by MATLAB createDAT_with_microbes.m",
                        f"Expected location: {geom_path}"
                    ]
                )
                self.finished.emit(-1)
                return
            
            # Check geometry file size
            geom_size = os.path.getsize(geom_path)
            expected_values = self.project.domain.nx * self.project.domain.ny * self.project.domain.nz
            self._log_and_emit(f"✓ Geometry file: {geom_file} ({geom_size:,} bytes)")
            
            # Validate geometry file content
            valid, geom_msg = self._validate_geometry_file(geom_path, expected_values)
            if not valid:
                self._emit_error(
                    "Geometry file validation failed",
                    geom_msg,
                    [
                        f"Expected {expected_values:,} values for {self.project.domain.nx}×{self.project.domain.ny}×{self.project.domain.nz} domain",
                        "Check that dimensions in GUI match the MATLAB script used to create the file.",
                        "The .dat file should contain only integer material numbers (0, 1, 2, 3...)."
                    ]
                )
                self.finished.emit(-1)
                return
            self._log_and_emit(f"✓ Geometry validated: {geom_msg}")
            
            # Check 5: XML configuration
            xml_path = self._find_xml_file(project_dir)
            if not xml_path:
                self._emit_error(
                    "XML configuration not found",
                    f"No CompLaB.xml file in: {project_dir}",
                    [
                        "Click 'Save' to generate the XML configuration file.",
                        "The XML file is created automatically when you save the project."
                    ]
                )
                self.finished.emit(-1)
                return
            self._log_and_emit(f"✓ XML configuration: {xml_path}")
            
            # Check 6: Validate XML content
            xml_valid, xml_msg = self._validate_xml(os.path.join(project_dir, xml_path))
            if not xml_valid:
                self._emit_error(
                    "XML validation failed",
                    xml_msg,
                    [
                        "The XML file may be corrupted or have invalid values.",
                        "Try saving the project again.",
                        "Check that all required fields are filled in."
                    ]
                )
                self.finished.emit(-1)
                return
            self._log_and_emit(f"✓ XML validated: {xml_msg}")
            
            # Create output directory
            output_dir = self.project.get_output_dir()
            os.makedirs(output_dir, exist_ok=True)
            self._log_and_emit(f"✓ Output directory: {output_dir}")
            
            # Setup log file
            self._setup_log_file()
            
            self._log_and_emit("")
            self._log_and_emit("=" * 60)
            self._log_and_emit("CompLaB Simulation Started")
            self._log_and_emit(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            self._log_and_emit("=" * 60)
            self._log_and_emit(f"Domain: {self.project.domain.nx} × {self.project.domain.ny} × {self.project.domain.nz}")
            self._log_and_emit(f"Substrates: {len(self.project.substrates)}")
            self._log_and_emit(f"Microbes: {len(self.project.microbes)}")
            self._log_and_emit("-" * 60)
            
            # === START SIMULATION ===
            self.process = QProcess()
            self.process.setWorkingDirectory(project_dir)
            self.process.setProcessChannelMode(QProcess.MergedChannels)
            self.process.readyReadStandardOutput.connect(self._handle_output)
            
            self.process.start(complab_exe, [xml_path])
            
            if not self.process.waitForStarted(10000):
                self._emit_error(
                    "Failed to start CompLaB",
                    "The process did not start within 10 seconds.",
                    [
                        "Check that complab.exe is not corrupted.",
                        "Try running complab.exe manually from command line.",
                        "Check Windows Event Viewer for application errors."
                    ]
                )
                self._close_log_file()
                self.finished.emit(-1)
                return
                
            self._log_and_emit("Process started successfully")
            self._log_and_emit("-" * 60)
            
            # Wait for completion
            while self.process.state() != QProcess.NotRunning:
                if self._stop_requested:
                    self._log_and_emit("\n*** Simulation stopped by user ***")
                    self.process.kill()
                    self.process.waitForFinished(5000)
                    break
                self.process.waitForReadyRead(100)
                
            # Get exit code and analyze
            exit_code = self.process.exitCode()
            
            self._log_and_emit("-" * 60)
            
            if exit_code == 0:
                self._log_and_emit("✓ Simulation completed successfully!")
            else:
                self._analyze_failure(exit_code)
                
            self._log_and_emit(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            self._log_and_emit("=" * 60)
            
            self._close_log_file()
            self.finished.emit(exit_code)
            
        except Exception as e:
            import traceback
            error_msg = f"Exception during simulation: {str(e)}\n{traceback.format_exc()}"
            self._log_and_emit(f"ERROR: {error_msg}")
            self.error.emit(error_msg)
            self._close_log_file()
            self.finished.emit(-1)
            
    def _validate_geometry_file(self, filepath: str, expected_values: int) -> Tuple[bool, str]:
        """Validate geometry file content"""
        try:
            line_count = 0
            invalid_lines = []
            min_val = float('inf')
            max_val = float('-inf')
            
            with open(filepath, 'r') as f:
                for i, line in enumerate(f):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        val = int(line)
                        line_count += 1
                        min_val = min(min_val, val)
                        max_val = max(max_val, val)
                    except ValueError:
                        if len(invalid_lines) < 5:
                            invalid_lines.append(f"Line {i+1}: '{line[:50]}'")
                            
            if invalid_lines:
                return False, f"Non-integer values found:\n" + "\n".join(invalid_lines)
                
            if line_count != expected_values:
                return False, f"Value count mismatch: file has {line_count:,}, expected {expected_values:,}"
                
            if min_val < 0:
                return False, f"Negative values found (min={min_val}). Material numbers must be >= 0."
                
            if max_val > 100:
                return False, f"Suspiciously high material number: {max_val}. Expected 0-10."
                
            return True, f"{line_count:,} values, materials {min_val}-{max_val}"
            
        except Exception as e:
            return False, f"Error reading file: {str(e)}"
            
    def _validate_xml(self, filepath: str) -> Tuple[bool, str]:
        """Validate XML configuration"""
        try:
            import xml.etree.ElementTree as ET
            tree = ET.parse(filepath)
            root = tree.getroot()
            
            # Check required sections
            required = ['path', 'LB_numerics', 'IO']
            missing = [r for r in required if root.find(r) is None]
            
            if missing:
                return False, f"Missing sections: {', '.join(missing)}"
                
            # Check domain settings
            lb = root.find('LB_numerics')
            domain = lb.find('domain') if lb is not None else None
            
            if domain is None:
                return False, "Missing domain configuration"
                
            # Verify geometry filename matches
            filename = domain.find('filename')
            if filename is not None:
                xml_geom = filename.text.strip()
                if xml_geom != self.project.domain.geometry_file:
                    return False, f"Geometry file mismatch: XML has '{xml_geom}', project has '{self.project.domain.geometry_file}'"
                    
            return True, "XML structure valid"
            
        except ET.ParseError as e:
            return False, f"XML parse error: {str(e)}"
        except Exception as e:
            return False, f"Error: {str(e)}"
            
    def _analyze_failure(self, exit_code: int):
        """Analyze simulation failure and provide helpful messages"""
        self._log_and_emit(f"\n✗ Simulation FAILED with exit code: {exit_code}")
        self._log_and_emit("")
        
        # Analyze exit code
        error_info = self._get_exit_code_info(exit_code)
        self._log_and_emit(f"Error Type: {error_info['type']}")
        self._log_and_emit(f"Description: {error_info['description']}")
        
        # Search output buffer for clues
        error_clues = self._search_output_for_errors()
        if error_clues:
            self._log_and_emit("\nError Details from Output:")
            for clue in error_clues:
                self._log_and_emit(f"  • {clue}")
        
        # Provide suggestions
        suggestions = error_info['suggestions'] + self._get_suggestions_from_output()
        if suggestions:
            self._log_and_emit("\nSuggestions:")
            for i, suggestion in enumerate(suggestions, 1):
                self._log_and_emit(f"  {i}. {suggestion}")
                
        # Emit error signal with full details
        error_msg = f"""
Simulation Failed (Exit Code: {exit_code})

{error_info['type']}: {error_info['description']}

{chr(10).join(error_clues) if error_clues else 'No additional error details captured.'}

Suggestions:
{chr(10).join(f'• {s}' for s in suggestions)}
"""
        self.error.emit(error_msg)
        
    def _get_exit_code_info(self, exit_code: int) -> dict:
        """Get information about specific exit codes"""
        # Common Windows exit codes
        exit_codes = {
            -1: {
                'type': 'General Error',
                'description': 'The program exited with an unspecified error.',
                'suggestions': [
                    'Check that all input files are valid.',
                    'Verify geometry file dimensions match project settings.',
                    'Run simulation from command line to see detailed error.'
                ]
            },
            -1073740940: {
                'type': 'Heap Corruption (0xC0000374)',
                'description': 'Memory corruption detected - usually caused by array bounds violation.',
                'suggestions': [
                    'Geometry file dimensions may not match nx, ny, nz settings.',
                    'Check that geometry file has exactly nx × ny × nz values.',
                    'Verify material numbers are valid (0, 1, 2, 3...).'
                ]
            },
            -1073741819: {
                'type': 'Access Violation (0xC0000005)',
                'description': 'Memory access error - program tried to read/write invalid memory.',
                'suggestions': [
                    'Geometry file may be corrupted or have wrong format.',
                    'Check domain dimensions match geometry file.',
                    'Try with a smaller domain size to test.'
                ]
            },
            -1073741571: {
                'type': 'Stack Overflow (0xC00000FD)',
                'description': 'Stack memory exhausted - domain may be too large.',
                'suggestions': [
                    'Reduce domain size (nx, ny, nz).',
                    'Close other applications to free memory.',
                    'Try running on a machine with more RAM.'
                ]
            },
            1: {
                'type': 'Configuration Error',
                'description': 'Invalid configuration or missing required parameters.',
                'suggestions': [
                    'Check XML file for missing or invalid values.',
                    'Ensure all required fields are specified.',
                    'Verify file paths are correct.'
                ]
            },
            2: {
                'type': 'File Not Found',
                'description': 'A required file could not be found.',
                'suggestions': [
                    'Check that geometry file exists in input folder.',
                    'Verify input/output paths in XML are correct.',
                    'Ensure file names match exactly (case-sensitive).'
                ]
            },
        }
        
        return exit_codes.get(exit_code, {
            'type': f'Unknown Error (Code: {exit_code})',
            'description': 'An unexpected error occurred.',
            'suggestions': [
                'Run simulation from command line for more details.',
                'Check the log file in the output folder.',
                'Try with default/simple settings first.'
            ]
        })
        
    def _search_output_for_errors(self) -> List[str]:
        """Search captured output for error messages"""
        errors = []
        error_patterns = [
            (r'[Ee]rror[:\s]+(.*)', 'Error'),
            (r'[Ff]ailed[:\s]+(.*)', 'Failed'),
            (r'[Cc]ould not[:\s]+(.*)', 'Could not'),
            (r'[Nn]ot found[:\s]*(.*)', 'Not found'),
            (r'[Ii]nvalid[:\s]+(.*)', 'Invalid'),
            (r'[Mm]ismatch[:\s]+(.*)', 'Mismatch'),
            (r'[Tt]erminating[:\s]+(.*)', 'Terminating'),
            (r'[Ee]xception[:\s]+(.*)', 'Exception'),
        ]
        
        for line in self._output_buffer:
            for pattern, prefix in error_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    errors.append(line.strip())
                    break
                    
        return errors[:10]  # Limit to first 10 errors
        
    def _get_suggestions_from_output(self) -> List[str]:
        """Get suggestions based on output content"""
        suggestions = []
        output_text = '\n'.join(self._output_buffer).lower()
        
        if 'geometry' in output_text and ('error' in output_text or 'fail' in output_text):
            suggestions.append("Verify geometry file format: one integer per line, no header.")
            
        if 'xml' in output_text or 'parameter' in output_text:
            suggestions.append("Check XML configuration - save project to regenerate XML.")
            
        if 'memory' in output_text or 'alloc' in output_text:
            suggestions.append("Try reducing domain size or closing other applications.")
            
        if 'file' in output_text and 'not' in output_text:
            suggestions.append("Check that all input files exist and paths are correct.")
            
        if len(self._output_buffer) < 5:
            suggestions.append("Very little output captured - simulation may have crashed immediately.")
            suggestions.append("Try running from command line: complab.exe CompLaB.xml")
            
        return suggestions
        
    def _emit_error(self, title: str, description: str, suggestions: List[str]):
        """Emit a formatted error message"""
        self._log_and_emit("")
        self._log_and_emit(f"✗ ERROR: {title}")
        self._log_and_emit(f"  {description}")
        self._log_and_emit("")
        self._log_and_emit("Suggestions:")
        for suggestion in suggestions:
            self._log_and_emit(f"  • {suggestion}")
        self._log_and_emit("")
        
        error_msg = f"{title}\n\n{description}\n\nSuggestions:\n" + "\n".join(f"• {s}" for s in suggestions)
        self.error.emit(error_msg)
        
    def _find_xml_file(self, project_dir: str) -> Optional[str]:
        """Find the XML configuration file"""
        possible_paths = [
            "CompLaB.xml",
            "input/config.xml",
            "input/CompLaB.xml",
            "config.xml",
        ]
        
        for rel_path in possible_paths:
            full_path = os.path.join(project_dir, rel_path)
            if os.path.exists(full_path):
                return rel_path
        return None
            
    def stop(self):
        """Request simulation stop"""
        self._stop_requested = True
        if self.process and self.process.state() != QProcess.NotRunning:
            self.process.terminate()
            if not self.process.waitForFinished(3000):
                self.process.kill()
                
    def _setup_log_file(self):
        """Create log file in project output directory"""
        try:
            output_dir = self.project.get_output_dir()
            os.makedirs(output_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            self._log_path = os.path.join(output_dir, f"simulation_{timestamp}.log")
            self._log_file = open(self._log_path, 'w', encoding='utf-8')
        except Exception as e:
            print(f"Warning: Could not create log file: {e}")
            self._log_file = None
            
    def _close_log_file(self):
        """Close the log file"""
        if self._log_file:
            try:
                if self._log_path:
                    self._log_and_emit(f"\nLog saved to: {self._log_path}")
                self._log_file.close()
            except:
                pass
            self._log_file = None
            
    def _log_and_emit(self, message: str):
        """Log message to file and emit to console"""
        self.output.emit(message)
        self._output_buffer.append(message)
        
        if self._log_file:
            try:
                self._log_file.write(message + "\n")
                self._log_file.flush()
            except:
                pass
                
    def _handle_output(self):
        """Handle process output"""
        if self.process:
            try:
                data = self.process.readAllStandardOutput().data().decode('utf-8', errors='replace')
                
                for line in data.split('\n'):
                    line = line.rstrip()
                    if line:
                        self._log_and_emit(line)
                        self._parse_progress(line)
            except Exception as e:
                self._log_and_emit(f"[Output error: {e}]")
                    
    def _parse_progress(self, line: str):
        """Parse progress from output line"""
        patterns = [
            r'iT\s*=\s*(\d+)',
            r'[Ii]teration[:\s]+(\d+)',
            r'Step[:\s]+(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, line)
            if match:
                iteration = int(match.group(1))
                self.progress.emit(iteration, f"Iteration {iteration}")
                break
                
        if "converge" in line.lower():
            self.progress.emit(0, "Checking convergence...")
        elif "completed" in line.lower():
            self.progress.emit(0, "Completed")
            
    def _find_complab_executable(self) -> Optional[str]:
        """Find CompLaB executable"""
        possible_paths = []
        
        if os.name == 'nt':
            local_appdata = os.environ.get("LOCALAPPDATA", "")
            user_home = os.environ.get("USERPROFILE", "")
            
            possible_paths.extend([
                os.path.join(local_appdata, "CompLaB_Studio", "bin", "complab.exe"),
                os.path.join(user_home, "CompLaB_Studio", "bin", "complab.exe"),
                os.path.join(local_appdata, "CompLaB", "complab.exe"),
                os.path.join(os.environ.get("PROGRAMFILES", ""), "CompLaB", "complab.exe"),
            ])
        else:
            user_home = os.path.expanduser("~")
            possible_paths.extend([
                os.path.join(user_home, ".local", "bin", "complab"),
                os.path.join(user_home, "CompLaB_Studio", "bin", "complab"),
                "/usr/local/bin/complab",
                "/usr/bin/complab",
            ])
            
        env_path = os.environ.get("COMPLAB_PATH", "")
        if env_path:
            possible_paths.insert(0, env_path)
            
        for path in possible_paths:
            if path and os.path.isfile(path):
                return path
        return None


class SimulationMonitor:
    """Monitor simulation progress and results"""
    
    def __init__(self, project: CompLaBProject):
        self.project = project
        self.current_iteration = 0
        self.total_iterations = project.iterations.ade_max_iT
        
    def update(self, iteration: int):
        self.current_iteration = iteration
        
    @property
    def progress_percent(self) -> float:
        if self.total_iterations > 0:
            return (self.current_iteration / self.total_iterations) * 100
        return 0
        
    def get_output_files(self):
        output_dir = self.project.get_output_dir()
        if not os.path.exists(output_dir):
            return []
        return sorted([
            os.path.join(output_dir, f) 
            for f in os.listdir(output_dir) 
            if f.endswith(('.vti', '.vtk', '.chk'))
        ])
        
    def get_log_files(self):
        output_dir = self.project.get_output_dir()
        if not os.path.exists(output_dir):
            return []
        return sorted([
            os.path.join(output_dir, f) 
            for f in os.listdir(output_dir) 
            if f.endswith('.log')
        ], reverse=True)
