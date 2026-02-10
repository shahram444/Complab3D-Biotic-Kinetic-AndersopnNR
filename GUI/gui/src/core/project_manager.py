"""
Project Manager - handles loading, saving, and exporting projects
"""

import os
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
import xml.etree.ElementTree as ET
from xml.dom import minidom

from .project import (
    CompLaBProject, DomainSettings, FluidSettings, IterationSettings,
    IOSettings, MicrobiologySettings, Substrate, Microbe,
    DiffusionCoefficients, BoundaryCondition, BoundaryType, SolverType,
    MicrobeDistribution, DistributionType, SimulationMode, ReactionType,
    EquilibriumSettings, EquilibriumSpecies
)

# Try to import templates (may not exist yet)
try:
    from .project_templates import TemplateType, apply_template
    HAS_TEMPLATES = True
except ImportError:
    HAS_TEMPLATES = False


class ProjectManager:
    """Manages CompLaB projects - loading, saving, import/export"""

    def __init__(self):
        pass

    def create_project(self, data: Dict[str, Any]) -> CompLaBProject:
        """Create a new project with given data"""
        project = CompLaBProject(data.get("name", "Untitled"))
        project.description = data.get("description", "")
        project.created = datetime.now().isoformat()
        project.modified = project.created

        # Set path if provided
        if "path" in data:
            project.path = data["path"]

            # Create project directory structure
            project_dir = os.path.dirname(project.path)
            os.makedirs(project_dir, exist_ok=True)
            os.makedirs(os.path.join(project_dir, "input"), exist_ok=True)
            os.makedirs(os.path.join(project_dir, "output"), exist_ok=True)

        # Apply template if specified
        template_type = data.get("template")
        if HAS_TEMPLATES and template_type:
            apply_template(project, template_type)
        else:
            # Default setup if no template
            if data.get("add_default_substrate", True):
                project.add_substrate(Substrate(
                    name="glucose",
                    diffusion_coefficients=DiffusionCoefficients(6e-10, 5e-10),
                    initial_concentration=1.0
                ))

            if data.get("add_default_microbe", True):
                project.add_microbe(Microbe(
                    name="bacteria",
                    solver_type=SolverType.CELLULAR_AUTOMATA,
                    reaction_type=ReactionType.KINETICS,
                    material_number=3,
                    initial_densities=[10.0],
                    half_saturation_constants=[0.1],
                    maximum_uptake_flux=[0.2, 5.0]
                ))

        # Save the project file immediately after creation
        if project.path:
            try:
                self.save_project(project)
            except Exception as e:
                print(f"Warning: Could not save project on creation: {e}")

        return project

    def save_project(self, project: CompLaBProject):
        """Save project to file"""
        if not project.path:
            raise ValueError("Project path not set")

        project.modified = datetime.now().isoformat()

        # Create directory if needed
        project_dir = os.path.dirname(project.path)
        if project_dir:
            os.makedirs(project_dir, exist_ok=True)

        # Save project file
        try:
            project_data = project.to_dict()
            with open(project.path, 'w') as f:
                json.dump(project_data, f, indent=2)
        except Exception as e:
            print(f"Error saving project: {e}")
            raise

        # Also export XML for CompLaB
        try:
            xml_path = project.get_xml_path()
            self.export_to_xml(project, xml_path)
        except Exception as e:
            print(f"Warning: Could not export XML: {e}")

    def load_project(self, path: str) -> CompLaBProject:
        """Load project from file"""
        with open(path, 'r') as f:
            data = json.load(f)

        project = CompLaBProject.from_dict(data)
        project.path = path

        return project

    def import_from_xml(self, xml_path: str) -> CompLaBProject:
        """Import project from CompLaB XML file"""
        tree = ET.parse(xml_path)
        root = tree.getroot()

        project = CompLaBProject("Imported Project")
        project.created = datetime.now().isoformat()

        # Parse path settings
        path_elem = root.find("path")
        if path_elem is not None:
            src = path_elem.find("src_path")
            if src is not None:
                project.src_path = src.text.strip()
            inp = path_elem.find("input_path")
            if inp is not None:
                project.input_path = inp.text.strip()
            out = path_elem.find("output_path")
            if out is not None:
                project.output_path = out.text.strip()

        # Parse simulation_mode
        sim_elem = root.find("simulation_mode")
        if sim_elem is not None:
            biotic = sim_elem.find("biotic_mode")
            if biotic is not None:
                val = biotic.text.strip().lower()
                project.simulation_mode.biotic_mode = val in ("true", "yes", "biotic", "1")
            kinetics = sim_elem.find("enable_kinetics")
            if kinetics is not None:
                val = kinetics.text.strip().lower()
                project.simulation_mode.enable_kinetics = val in ("true", "yes", "1")
            abiotic = sim_elem.find("enable_abiotic_kinetics")
            if abiotic is not None:
                val = abiotic.text.strip().lower()
                project.simulation_mode.enable_abiotic_kinetics = val in ("true", "yes", "1")
            diag = sim_elem.find("enable_validation_diagnostics")
            if diag is not None:
                val = diag.text.strip().lower()
                project.simulation_mode.enable_validation_diagnostics = val in ("true", "yes", "1")

        # Parse LB numerics
        lb_elem = root.find("LB_numerics")
        if lb_elem is not None:
            delta_p = lb_elem.find("delta_P")
            if delta_p is not None:
                project.fluid.delta_p = float(delta_p.text.strip())
            peclet = lb_elem.find("Peclet")
            if peclet is not None:
                project.fluid.peclet = float(peclet.text.strip())
            tau = lb_elem.find("tau")
            if tau is not None:
                project.fluid.tau = float(tau.text.strip())
            perf = lb_elem.find("track_performance")
            if perf is not None:
                val = perf.text.strip().lower()
                project.io.track_performance = val in ("true", "yes", "1")

            # Domain
            domain_elem = lb_elem.find("domain")
            if domain_elem is not None:
                for tag, attr in [("nx", "nx"), ("ny", "ny"), ("nz", "nz")]:
                    el = domain_elem.find(tag)
                    if el is not None:
                        setattr(project.domain, attr, int(el.text.strip()))
                dx_el = domain_elem.find("dx")
                if dx_el is not None:
                    project.domain.dx = float(dx_el.text.strip())
                    project.domain.dy = project.domain.dx
                    project.domain.dz = project.domain.dx
                unit_el = domain_elem.find("unit")
                if unit_el is not None:
                    project.domain.unit = unit_el.text.strip()
                cl_el = domain_elem.find("characteristic_length")
                if cl_el is not None:
                    project.domain.characteristic_length = float(cl_el.text.strip())
                fn_el = domain_elem.find("filename")
                if fn_el is not None:
                    project.domain.geometry_file = fn_el.text.strip()

                # Material numbers
                mat_elem = domain_elem.find("material_numbers")
                if mat_elem is not None:
                    pore = mat_elem.find("pore")
                    if pore is not None:
                        project.domain.pore_material = int(pore.text.strip())
                    solid = mat_elem.find("solid")
                    if solid is not None:
                        project.domain.solid_material = int(solid.text.strip())
                    bb = mat_elem.find("bounce_back")
                    if bb is not None:
                        project.domain.bounce_back_material = int(bb.text.strip())

            # Iteration settings
            iter_elem = lb_elem.find("iteration")
            if iter_elem is not None:
                iter_map = {
                    "ns_rerun_iT0": ("ns_rerun_iT0", int),
                    "ns_max_iT1": ("ns_max_iT1", int),
                    "ns_max_iT2": ("ns_max_iT2", int),
                    "ns_converge_iT1": ("ns_converge_iT1", float),
                    "ns_converge_iT2": ("ns_converge_iT2", float),
                    "ns_update_interval": ("ns_update_interval", int),
                    "ade_rerun_iT0": ("ade_rerun_iT0", int),
                    "ade_max_iT": ("ade_max_iT", int),
                    "ade_converge_iT": ("ade_converge_iT", float),
                    "ade_update_interval": ("ade_update_interval", int),
                }
                for xml_tag, (attr, conv) in iter_map.items():
                    el = iter_elem.find(xml_tag)
                    if el is not None:
                        setattr(project.iterations, attr, conv(el.text.strip()))

        # Parse chemistry
        chem_elem = root.find("chemistry")
        if chem_elem is not None:
            nsubs_el = chem_elem.find("number_of_substrates")
            nsubs = int(nsubs_el.text.strip()) if nsubs_el is not None else 0
            for i in range(nsubs):
                sub_elem = chem_elem.find(f"substrate{i}")
                if sub_elem is not None:
                    sub = Substrate()
                    name_el = sub_elem.find("name_of_substrates")
                    if name_el is not None:
                        sub.name = name_el.text.strip()
                    ic_el = sub_elem.find("initial_concentration")
                    if ic_el is not None:
                        sub.initial_concentration = float(ic_el.text.strip())
                    diff_elem = sub_elem.find("substrate_diffusion_coefficients")
                    if diff_elem is not None:
                        pore = diff_elem.find("in_pore")
                        bio = diff_elem.find("in_biofilm")
                        sub.diffusion_coefficients = DiffusionCoefficients(
                            float(pore.text.strip()) if pore is not None else 1e-9,
                            float(bio.text.strip()) if bio is not None else 1e-10
                        )
                    lbt_el = sub_elem.find("left_boundary_type")
                    lbv_el = sub_elem.find("left_boundary_condition")
                    if lbt_el is not None:
                        sub.left_boundary = BoundaryCondition(
                            BoundaryType(lbt_el.text.strip()),
                            float(lbv_el.text.strip()) if lbv_el is not None else 0.0
                        )
                    rbt_el = sub_elem.find("right_boundary_type")
                    rbv_el = sub_elem.find("right_boundary_condition")
                    if rbt_el is not None:
                        sub.right_boundary = BoundaryCondition(
                            BoundaryType(rbt_el.text.strip()),
                            float(rbv_el.text.strip()) if rbv_el is not None else 0.0
                        )
                    project.substrates.append(sub)

        # Parse microbiology
        bio_elem = root.find("microbiology")
        if bio_elem is not None:
            nmics_el = bio_elem.find("number_of_microbes")
            nmics = int(nmics_el.text.strip()) if nmics_el is not None else 0
            mbm_el = bio_elem.find("maximum_biomass_density")
            if mbm_el is not None:
                project.microbiology.maximum_biomass_density = float(mbm_el.text.strip())
            thrd_el = bio_elem.find("thrd_biofilm_fraction")
            if thrd_el is not None:
                project.microbiology.thrd_biofilm_fraction = float(thrd_el.text.strip())
            ca_el = bio_elem.find("CA_method")
            if ca_el is not None:
                project.microbiology.ca_method = ca_el.text.strip()

            for i in range(nmics):
                mic_elem = bio_elem.find(f"microbe{i}")
                if mic_elem is not None:
                    mic = Microbe()
                    name_el = mic_elem.find("name_of_microbes")
                    if name_el is not None:
                        mic.name = name_el.text.strip()
                    st_el = mic_elem.find("solver_type")
                    if st_el is not None:
                        try:
                            mic.solver_type = SolverType(st_el.text.strip())
                        except ValueError:
                            mic.solver_type = SolverType.CELLULAR_AUTOMATA
                    rt_el = mic_elem.find("reaction_type")
                    if rt_el is not None:
                        try:
                            mic.reaction_type = ReactionType(rt_el.text.strip())
                        except ValueError:
                            mic.reaction_type = ReactionType.KINETICS
                    id_el = mic_elem.find("initial_densities")
                    if id_el is not None:
                        mic.initial_densities = [float(x) for x in id_el.text.strip().split()]
                    dc_el = mic_elem.find("decay_coefficient")
                    if dc_el is not None:
                        mic.decay_coefficient = float(dc_el.text.strip())
                    vr_el = mic_elem.find("viscosity_ratio_in_biofilm")
                    if vr_el is not None:
                        mic.viscosity_ratio_in_biofilm = float(vr_el.text.strip())
                    ks_el = mic_elem.find("half_saturation_constants")
                    if ks_el is not None:
                        mic.half_saturation_constants = [float(x) for x in ks_el.text.strip().split()]
                    vm_el = mic_elem.find("maximum_uptake_flux")
                    if vm_el is not None:
                        mic.maximum_uptake_flux = [float(x) for x in vm_el.text.strip().split()]
                    lbt_el = mic_elem.find("left_boundary_type")
                    lbv_el = mic_elem.find("left_boundary_condition")
                    if lbt_el is not None:
                        mic.left_boundary = BoundaryCondition(
                            BoundaryType(lbt_el.text.strip()),
                            float(lbv_el.text.strip()) if lbv_el is not None else 0.0
                        )
                    rbt_el = mic_elem.find("right_boundary_type")
                    rbv_el = mic_elem.find("right_boundary_condition")
                    if rbt_el is not None:
                        mic.right_boundary = BoundaryCondition(
                            BoundaryType(rbt_el.text.strip()),
                            float(rbv_el.text.strip()) if rbv_el is not None else 0.0
                        )
                    project.microbes.append(mic)

        # Parse equilibrium
        eq_elem = root.find("equilibrium")
        if eq_elem is not None:
            en_el = eq_elem.find("enabled")
            if en_el is not None:
                val = en_el.text.strip().lower()
                project.equilibrium.enabled = val in ("true", "yes", "1")
            comp_el = eq_elem.find("components")
            if comp_el is not None:
                project.equilibrium.components = int(comp_el.text.strip())
            # Parse stoichiometry
            stoich_elem = eq_elem.find("stoichiometry")
            logk_elem = eq_elem.find("logK")
            if stoich_elem is not None:
                num_subs = len(project.substrates)
                for i in range(num_subs):
                    sp = EquilibriumSpecies()
                    s_el = stoich_elem.find(f"species{i}")
                    if s_el is not None:
                        sp.stoichiometry = [float(x) for x in s_el.text.strip().split()]
                    lk_el = logk_elem.find(f"species{i}") if logk_elem is not None else None
                    if lk_el is not None:
                        sp.logK = float(lk_el.text.strip())
                    project.equilibrium.species.append(sp)

        # Parse IO
        io_elem = root.find("IO")
        if io_elem is not None:
            rns = io_elem.find("read_NS_file")
            if rns is not None:
                val = rns.text.strip().lower()
                project.io.read_ns_file = val in ("true", "yes", "1")
            rade = io_elem.find("read_ADE_file")
            if rade is not None:
                val = rade.text.strip().lower()
                project.io.read_ade_file = val in ("true", "yes", "1")
            for tag, attr in [("ns_filename", "ns_filename"), ("mask_filename", "mask_filename"),
                              ("subs_filename", "subs_filename"), ("bio_filename", "bio_filename")]:
                el = io_elem.find(tag)
                if el is not None:
                    setattr(project.io, attr, el.text.strip())
            vtk_el = io_elem.find("save_VTK_interval")
            if vtk_el is not None:
                project.io.save_vtk_interval = int(vtk_el.text.strip())
            chk_el = io_elem.find("save_CHK_interval")
            if chk_el is not None:
                project.io.save_chk_interval = int(chk_el.text.strip())

        return project

    def export_to_xml(self, project: CompLaBProject, xml_path: str):
        """Export project to CompLaB XML format matching C++ parser exactly"""
        root = ET.Element("parameters")

        # <path> section - must include src_path
        path_elem = ET.SubElement(root, "path")
        ET.SubElement(path_elem, "src_path").text = project.src_path
        ET.SubElement(path_elem, "input_path").text = project.input_path
        ET.SubElement(path_elem, "output_path").text = project.output_path

        # <simulation_mode> section
        sim_elem = ET.SubElement(root, "simulation_mode")
        ET.SubElement(sim_elem, "biotic_mode").text = "true" if project.simulation_mode.biotic_mode else "false"
        ET.SubElement(sim_elem, "enable_kinetics").text = "true" if project.simulation_mode.enable_kinetics else "false"
        ET.SubElement(sim_elem, "enable_abiotic_kinetics").text = "true" if project.simulation_mode.enable_abiotic_kinetics else "false"
        ET.SubElement(sim_elem, "enable_validation_diagnostics").text = "true" if project.simulation_mode.enable_validation_diagnostics else "false"

        # <LB_numerics> section
        lb_elem = ET.SubElement(root, "LB_numerics")

        # Domain
        domain_elem = ET.SubElement(lb_elem, "domain")
        ET.SubElement(domain_elem, "nx").text = str(project.domain.nx)
        ET.SubElement(domain_elem, "ny").text = str(project.domain.ny)
        ET.SubElement(domain_elem, "nz").text = str(project.domain.nz)
        ET.SubElement(domain_elem, "dx").text = str(project.domain.dx)
        ET.SubElement(domain_elem, "unit").text = project.domain.unit
        ET.SubElement(domain_elem, "characteristic_length").text = str(project.domain.characteristic_length)
        ET.SubElement(domain_elem, "filename").text = project.domain.geometry_file

        # Material numbers
        mat_elem = ET.SubElement(domain_elem, "material_numbers")
        ET.SubElement(mat_elem, "pore").text = str(project.domain.pore_material)
        ET.SubElement(mat_elem, "solid").text = str(project.domain.solid_material)
        ET.SubElement(mat_elem, "bounce_back").text = str(project.domain.bounce_back_material)
        for i, microbe in enumerate(project.microbes):
            mat_vals = [str(microbe.material_number)]
            # Microbe can have multiple material numbers (film + planktonic)
            if len(microbe.initial_densities) > 1:
                mat_vals.append(str(microbe.material_number + 3))
            ET.SubElement(mat_elem, f"microbe{i}").text = " ".join(mat_vals)

        # Fluid settings
        ET.SubElement(lb_elem, "delta_P").text = str(project.fluid.delta_p)
        ET.SubElement(lb_elem, "Peclet").text = str(project.fluid.peclet)
        ET.SubElement(lb_elem, "tau").text = str(project.fluid.tau)
        ET.SubElement(lb_elem, "track_performance").text = "true" if project.io.track_performance else "false"

        # Iteration
        iter_elem = ET.SubElement(lb_elem, "iteration")
        ET.SubElement(iter_elem, "ns_max_iT1").text = str(project.iterations.ns_max_iT1)
        ET.SubElement(iter_elem, "ns_max_iT2").text = str(project.iterations.ns_max_iT2)
        ET.SubElement(iter_elem, "ns_converge_iT1").text = str(project.iterations.ns_converge_iT1)
        ET.SubElement(iter_elem, "ns_converge_iT2").text = str(project.iterations.ns_converge_iT2)
        ET.SubElement(iter_elem, "ade_max_iT").text = str(project.iterations.ade_max_iT)
        ET.SubElement(iter_elem, "ade_converge_iT").text = str(project.iterations.ade_converge_iT)
        ET.SubElement(iter_elem, "ns_update_interval").text = str(project.iterations.ns_update_interval)
        ET.SubElement(iter_elem, "ade_update_interval").text = str(project.iterations.ade_update_interval)

        # <chemistry> section
        chem_elem = ET.SubElement(root, "chemistry")
        ET.SubElement(chem_elem, "number_of_substrates").text = str(len(project.substrates))

        for i, substrate in enumerate(project.substrates):
            sub_elem = ET.SubElement(chem_elem, f"substrate{i}")
            ET.SubElement(sub_elem, "name_of_substrates").text = substrate.name
            ET.SubElement(sub_elem, "initial_concentration").text = str(substrate.initial_concentration)

            diff_elem = ET.SubElement(sub_elem, "substrate_diffusion_coefficients")
            ET.SubElement(diff_elem, "in_pore").text = str(substrate.diffusion_coefficients.in_pore)
            ET.SubElement(diff_elem, "in_biofilm").text = str(substrate.diffusion_coefficients.in_biofilm)

            ET.SubElement(sub_elem, "left_boundary_type").text = substrate.left_boundary.bc_type.value
            ET.SubElement(sub_elem, "right_boundary_type").text = substrate.right_boundary.bc_type.value
            ET.SubElement(sub_elem, "left_boundary_condition").text = str(substrate.left_boundary.value)
            ET.SubElement(sub_elem, "right_boundary_condition").text = str(substrate.right_boundary.value)

        # <microbiology> section
        bio_elem = ET.SubElement(root, "microbiology")
        ET.SubElement(bio_elem, "number_of_microbes").text = str(len(project.microbes))
        ET.SubElement(bio_elem, "maximum_biomass_density").text = str(project.microbiology.maximum_biomass_density)
        ET.SubElement(bio_elem, "thrd_biofilm_fraction").text = str(project.microbiology.thrd_biofilm_fraction)
        ET.SubElement(bio_elem, "CA_method").text = project.microbiology.ca_method

        for i, microbe in enumerate(project.microbes):
            mic_elem = ET.SubElement(bio_elem, f"microbe{i}")
            ET.SubElement(mic_elem, "name_of_microbes").text = microbe.name
            ET.SubElement(mic_elem, "solver_type").text = microbe.solver_type.value
            ET.SubElement(mic_elem, "reaction_type").text = microbe.reaction_type.value
            ET.SubElement(mic_elem, "initial_densities").text = " ".join(str(d) for d in microbe.initial_densities)
            ET.SubElement(mic_elem, "decay_coefficient").text = str(microbe.decay_coefficient)
            ET.SubElement(mic_elem, "viscosity_ratio_in_biofilm").text = str(microbe.viscosity_ratio_in_biofilm)
            ET.SubElement(mic_elem, "half_saturation_constants").text = " ".join(str(k) for k in microbe.half_saturation_constants)
            ET.SubElement(mic_elem, "maximum_uptake_flux").text = " ".join(str(v) for v in microbe.maximum_uptake_flux)

            ET.SubElement(mic_elem, "left_boundary_type").text = microbe.left_boundary.bc_type.value
            ET.SubElement(mic_elem, "right_boundary_type").text = microbe.right_boundary.bc_type.value
            ET.SubElement(mic_elem, "left_boundary_condition").text = str(microbe.left_boundary.value)
            ET.SubElement(mic_elem, "right_boundary_condition").text = str(microbe.right_boundary.value)

        # <equilibrium> section
        eq_elem = ET.SubElement(root, "equilibrium")
        ET.SubElement(eq_elem, "enabled").text = "true" if project.equilibrium.enabled else "false"
        if project.equilibrium.enabled:
            ET.SubElement(eq_elem, "components").text = str(project.equilibrium.components)
            if project.equilibrium.species:
                stoich_elem = ET.SubElement(eq_elem, "stoichiometry")
                logk_elem = ET.SubElement(eq_elem, "logK")
                for i, sp in enumerate(project.equilibrium.species):
                    ET.SubElement(stoich_elem, f"species{i}").text = " ".join(str(x) for x in sp.stoichiometry)
                    ET.SubElement(logk_elem, f"species{i}").text = str(sp.logK)

        # <IO> section
        io_elem = ET.SubElement(root, "IO")
        ET.SubElement(io_elem, "read_NS_file").text = "true" if project.io.read_ns_file else "false"
        ET.SubElement(io_elem, "read_ADE_file").text = "true" if project.io.read_ade_file else "false"
        ET.SubElement(io_elem, "ns_filename").text = project.io.ns_filename
        ET.SubElement(io_elem, "mask_filename").text = project.io.mask_filename
        ET.SubElement(io_elem, "subs_filename").text = project.io.subs_filename
        ET.SubElement(io_elem, "bio_filename").text = project.io.bio_filename
        ET.SubElement(io_elem, "save_VTK_interval").text = str(project.io.save_vtk_interval)
        ET.SubElement(io_elem, "save_CHK_interval").text = str(project.io.save_chk_interval)

        # Write XML with proper formatting
        xml_str = minidom.parseString(ET.tostring(root, encoding="unicode")).toprettyxml(indent="    ")

        # Remove extra XML declaration and blank lines
        lines = xml_str.split('\n')
        cleaned = []
        for line in lines:
            if line.strip():
                cleaned.append(line)
        xml_str = '<?xml version="1.0" ?>\n' + '\n'.join(
            l for l in cleaned if not l.startswith('<?xml')
        ) + '\n'

        with open(xml_path, 'w') as f:
            f.write(xml_str)
