"""I/O settings panel - checkpoint, VTK output, restart files."""

from .base_panel import BasePanel


class IOPanel(BasePanel):
    """Input/output settings: VTK interval, checkpoint interval, restart files."""

    def __init__(self, parent=None):
        super().__init__("I/O Settings", parent)
        self._build_ui()

    def _build_ui(self):
        self.add_section("Output Intervals")
        form = self.add_form()

        self.vtk_interval = self.make_spin(1000, 1)
        self.vtk_interval.setToolTip(
            "Save VTK output every N ADE iterations.\n"
            "Lower = more output files, more disk usage.\n"
            "C++ default: 1000.")
        form.addRow("VTK save interval:", self.vtk_interval)

        self.chk_interval = self.make_spin(1000000, 1)
        self.chk_interval.setToolTip(
            "Save checkpoint files every N ADE iterations.\n"
            "Used for restart capability.\n"
            "C++ default: 1000000.")
        form.addRow("Checkpoint interval:", self.chk_interval)

        self.add_section("Restart Files")
        form2 = self.add_form()

        self.read_ns = self.make_checkbox("Read NS restart file")
        self.read_ns.setToolTip("Load Navier-Stokes lattice from checkpoint file.")
        form2.addRow("", self.read_ns)

        self.read_ade = self.make_checkbox("Read ADE restart file")
        self.read_ade.setToolTip("Load ADE lattice from checkpoint file.")
        form2.addRow("", self.read_ade)

        self.add_section("Filenames")
        form3 = self.add_form()

        self.ns_file = self.make_line_edit("nsLattice")
        self.ns_file.setToolTip("Navier-Stokes checkpoint filename (without extension).")
        form3.addRow("NS filename:", self.ns_file)

        self.mask_file = self.make_line_edit("maskLattice")
        self.mask_file.setToolTip("Mask/geometry lattice filename.")
        form3.addRow("Mask filename:", self.mask_file)

        self.subs_file = self.make_line_edit("subsLattice")
        self.subs_file.setToolTip("Substrate lattice checkpoint filename.")
        form3.addRow("Substrate filename:", self.subs_file)

        self.bio_file = self.make_line_edit("bioLattice")
        self.bio_file.setToolTip("Biomass lattice checkpoint filename.")
        form3.addRow("Biomass filename:", self.bio_file)

        self.add_stretch()

    def load_from_project(self, project):
        io = project.io_settings
        self.vtk_interval.setValue(io.save_vtk_interval)
        self.chk_interval.setValue(io.save_chk_interval)
        self.read_ns.setChecked(io.read_ns_file)
        self.read_ade.setChecked(io.read_ade_file)
        self.ns_file.setText(io.ns_filename)
        self.mask_file.setText(io.mask_filename)
        self.subs_file.setText(io.subs_filename)
        self.bio_file.setText(io.bio_filename)

    def save_to_project(self, project):
        io = project.io_settings
        io.save_vtk_interval = self.vtk_interval.value()
        io.save_chk_interval = self.chk_interval.value()
        io.read_ns_file = self.read_ns.isChecked()
        io.read_ade_file = self.read_ade.isChecked()
        io.ns_filename = self.ns_file.text()
        io.mask_filename = self.mask_file.text()
        io.subs_filename = self.subs_file.text()
        io.bio_filename = self.bio_file.text()
