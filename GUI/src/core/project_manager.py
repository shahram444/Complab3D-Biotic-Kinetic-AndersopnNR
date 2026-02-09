"""Project save/load and XML import/export."""

import json
import os
import datetime
import xml.etree.ElementTree as ET
from pathlib import Path

from .project import (
    CompLaBProject, SimulationMode, PathSettings, DomainSettings,
    FluidSettings, IterationSettings, IOSettings, Substrate, Microbe,
    MicrobiologySettings, EquilibriumSettings,
)


class ProjectManager:

    @staticmethod
    def create_project(name, directory, template_data=None):
        proj_dir = Path(directory) / name
        proj_dir.mkdir(parents=True, exist_ok=True)
        (proj_dir / "input").mkdir(exist_ok=True)
        (proj_dir / "output").mkdir(exist_ok=True)

        if template_data is not None:
            proj = CompLaBProject.from_dict(template_data)
        else:
            proj = CompLaBProject()

        proj.name = name
        proj.project_dir = str(proj_dir)
        proj.created = datetime.datetime.now().isoformat(timespec="seconds")
        proj.modified = proj.created
        return proj

    @staticmethod
    def save_project(project, filepath=None):
        if filepath is None:
            filepath = Path(project.project_dir) / f"{project.name}.complab"
        project.stamp_modified()
        with open(filepath, "w") as f:
            json.dump(project.to_dict(), f, indent=2)
        xml_path = Path(project.project_dir) / "CompLaB.xml"
        ProjectManager.export_to_xml(project, str(xml_path))
        return str(filepath)

    @staticmethod
    def load_project(filepath):
        with open(filepath, "r") as f:
            data = json.load(f)
        proj = CompLaBProject.from_dict(data)
        if not proj.project_dir:
            proj.project_dir = str(Path(filepath).parent)
        return proj

    @staticmethod
    def export_to_xml(project, filepath):
        root = ET.Element("parameters")
        p = project

        # Path
        path_el = ET.SubElement(root, "path")
        ET.SubElement(path_el, "src_path").text = p.paths.src_path
        ET.SubElement(path_el, "input_path").text = p.paths.input_path
        ET.SubElement(path_el, "output_path").text = p.paths.output_path

        # Simulation mode
        sm_el = ET.SubElement(root, "simulation_mode")
        ET.SubElement(sm_el, "biotic_mode").text = str(p.simulation_mode.biotic_mode).lower()
        ET.SubElement(sm_el, "enable_kinetics").text = str(p.simulation_mode.enable_kinetics).lower()
        ET.SubElement(sm_el, "enable_abiotic_kinetics").text = str(p.simulation_mode.enable_abiotic_kinetics).lower()
        ET.SubElement(sm_el, "enable_validation_diagnostics").text = str(p.simulation_mode.enable_validation_diagnostics).lower()

        # LB_numerics
        lb = ET.SubElement(root, "LB_numerics")
        domain = ET.SubElement(lb, "domain")
        ET.SubElement(domain, "nx").text = str(p.domain.nx)
        ET.SubElement(domain, "ny").text = str(p.domain.ny)
        ET.SubElement(domain, "nz").text = str(p.domain.nz)
        ET.SubElement(domain, "dx").text = str(p.domain.dx)
        ET.SubElement(domain, "unit").text = p.domain.unit
        ET.SubElement(domain, "characteristic_length").text = str(p.domain.characteristic_length)
        ET.SubElement(domain, "filename").text = p.domain.geometry_file

        mat = ET.SubElement(domain, "material_numbers")
        ET.SubElement(mat, "pore").text = str(p.domain.pore_material)
        ET.SubElement(mat, "solid").text = str(p.domain.solid_material)
        ET.SubElement(mat, "bounce_back").text = str(p.domain.bounce_back_material)
        for i, m in enumerate(p.microbes):
            ET.SubElement(mat, f"microbe{i}").text = m.material_numbers

        ET.SubElement(lb, "delta_P").text = _sci(p.fluid.delta_p)
        ET.SubElement(lb, "Peclet").text = str(p.fluid.peclet)
        ET.SubElement(lb, "tau").text = str(p.fluid.tau)
        ET.SubElement(lb, "track_performance").text = str(p.track_performance).lower()

        it_el = ET.SubElement(lb, "iteration")
        ET.SubElement(it_el, "ns_max_iT1").text = str(p.iteration.ns_max_iT1)
        ET.SubElement(it_el, "ns_max_iT2").text = str(p.iteration.ns_max_iT2)
        ET.SubElement(it_el, "ns_converge_iT1").text = _sci(p.iteration.ns_converge_iT1)
        ET.SubElement(it_el, "ns_converge_iT2").text = _sci(p.iteration.ns_converge_iT2)
        ET.SubElement(it_el, "ade_max_iT").text = str(p.iteration.ade_max_iT)
        ET.SubElement(it_el, "ade_converge_iT").text = _sci(p.iteration.ade_converge_iT)
        ET.SubElement(it_el, "ns_update_interval").text = str(p.iteration.ns_update_interval)
        ET.SubElement(it_el, "ade_update_interval").text = str(p.iteration.ade_update_interval)

        # Chemistry
        chem = ET.SubElement(root, "chemistry")
        ET.SubElement(chem, "number_of_substrates").text = str(len(p.substrates))
        for i, s in enumerate(p.substrates):
            se = ET.SubElement(chem, f"substrate{i}")
            ET.SubElement(se, "name_of_substrates").text = s.name
            ET.SubElement(se, "initial_concentration").text = _sci(s.initial_concentration)
            diff = ET.SubElement(se, "substrate_diffusion_coefficients")
            ET.SubElement(diff, "in_pore").text = _sci(s.diffusion_in_pore)
            ET.SubElement(diff, "in_biofilm").text = _sci(s.diffusion_in_biofilm)
            ET.SubElement(se, "left_boundary_type").text = s.left_bc_type
            ET.SubElement(se, "right_boundary_type").text = s.right_bc_type
            ET.SubElement(se, "left_boundary_condition").text = _sci(s.left_bc_value)
            ET.SubElement(se, "right_boundary_condition").text = _sci(s.right_bc_value)

        # Microbiology
        if p.simulation_mode.biotic_mode:
            micro = ET.SubElement(root, "microbiology")
            ET.SubElement(micro, "number_of_microbes").text = str(len(p.microbes))
            ET.SubElement(micro, "maximum_biomass_density").text = str(p.microbiology.max_biomass_density)
            ET.SubElement(micro, "thrd_biofilm_fraction").text = str(p.microbiology.thrd_biofilm_fraction)
            ET.SubElement(micro, "CA_method").text = p.microbiology.ca_method

            for i, m in enumerate(p.microbes):
                me = ET.SubElement(micro, f"microbe{i}")
                ET.SubElement(me, "name_of_microbes").text = m.name
                ET.SubElement(me, "solver_type").text = m.solver_type
                ET.SubElement(me, "reaction_type").text = m.reaction_type
                ET.SubElement(me, "initial_densities").text = m.initial_densities
                ET.SubElement(me, "decay_coefficient").text = _sci(m.decay_coefficient)
                ET.SubElement(me, "viscosity_ratio_in_biofilm").text = str(m.viscosity_ratio)
                ET.SubElement(me, "half_saturation_constants").text = m.half_saturation_constants
                ET.SubElement(me, "maximum_uptake_flux").text = m.max_uptake_flux
                ET.SubElement(me, "left_boundary_type").text = m.left_bc_type
                ET.SubElement(me, "right_boundary_type").text = m.right_bc_type
                ET.SubElement(me, "left_boundary_condition").text = _sci(m.left_bc_value)
                ET.SubElement(me, "right_boundary_condition").text = _sci(m.right_bc_value)

        # Equilibrium
        eq_el = ET.SubElement(root, "equilibrium")
        ET.SubElement(eq_el, "enabled").text = str(p.equilibrium.enabled).lower()
        if p.equilibrium.enabled and p.equilibrium.components:
            ET.SubElement(eq_el, "components").text = " ".join(p.equilibrium.components)
            stoich = ET.SubElement(eq_el, "stoichiometry")
            for i, row in enumerate(p.equilibrium.stoichiometry):
                ET.SubElement(stoich, f"species{i}").text = " ".join(str(v) for v in row)
            logk = ET.SubElement(eq_el, "logK")
            for i, val in enumerate(p.equilibrium.log_k):
                ET.SubElement(logk, f"species{i}").text = str(val)

        # IO
        io_el = ET.SubElement(root, "IO")
        ET.SubElement(io_el, "read_NS_file").text = str(p.io_settings.read_ns_file).lower()
        ET.SubElement(io_el, "read_ADE_file").text = str(p.io_settings.read_ade_file).lower()
        ET.SubElement(io_el, "ns_filename").text = p.io_settings.ns_filename
        ET.SubElement(io_el, "mask_filename").text = p.io_settings.mask_filename
        ET.SubElement(io_el, "subs_filename").text = p.io_settings.subs_filename
        ET.SubElement(io_el, "bio_filename").text = p.io_settings.bio_filename
        ET.SubElement(io_el, "save_VTK_interval").text = str(p.io_settings.save_vtk_interval)
        ET.SubElement(io_el, "save_CHK_interval").text = str(p.io_settings.save_chk_interval)

        _indent_xml(root)
        tree = ET.ElementTree(root)
        tree.write(filepath, encoding="unicode", xml_declaration=True)

    @staticmethod
    def import_from_xml(filepath):
        """Parse a CompLaB.xml and return a CompLaBProject."""
        tree = ET.parse(filepath)
        root = tree.getroot()
        proj = CompLaBProject()
        proj.project_dir = str(Path(filepath).parent)
        proj.name = Path(filepath).parent.name

        # Paths
        path_el = root.find("path")
        if path_el is not None:
            proj.paths.src_path = _text(path_el, "src_path", "src")
            proj.paths.input_path = _text(path_el, "input_path", "input")
            proj.paths.output_path = _text(path_el, "output_path", "output")

        # Simulation mode
        sm_el = root.find("simulation_mode")
        if sm_el is not None:
            proj.simulation_mode.biotic_mode = _bool(sm_el, "biotic_mode", True)
            proj.simulation_mode.enable_kinetics = _bool(sm_el, "enable_kinetics", True)
            proj.simulation_mode.enable_abiotic_kinetics = _bool(sm_el, "enable_abiotic_kinetics", False)
            proj.simulation_mode.enable_validation_diagnostics = _bool(sm_el, "enable_validation_diagnostics", False)

        # LB_numerics
        lb = root.find("LB_numerics")
        if lb is not None:
            dom = lb.find("domain")
            if dom is not None:
                proj.domain.nx = _int(dom, "nx", 50)
                proj.domain.ny = _int(dom, "ny", 30)
                proj.domain.nz = _int(dom, "nz", 30)
                proj.domain.dx = _float(dom, "dx", 1.0)
                proj.domain.unit = _text(dom, "unit", "um")
                proj.domain.characteristic_length = _float(dom, "characteristic_length", 30.0)
                proj.domain.geometry_file = _text(dom, "filename", "geometry.dat")
                mat_el = dom.find("material_numbers")
                if mat_el is not None:
                    proj.domain.pore_material = _int(mat_el, "pore", 2)
                    proj.domain.solid_material = _int(mat_el, "solid", 0)
                    proj.domain.bounce_back_material = _int(mat_el, "bounce_back", 1)

            proj.fluid.delta_p = _float(lb, "delta_P", 2.0e-3)
            proj.fluid.peclet = _float(lb, "Peclet", 1.0)
            proj.fluid.tau = _float(lb, "tau", 0.8)
            proj.track_performance = _bool(lb, "track_performance", False)

            it_el = lb.find("iteration")
            if it_el is not None:
                proj.iteration.ns_max_iT1 = _int(it_el, "ns_max_iT1", 100000)
                proj.iteration.ns_max_iT2 = _int(it_el, "ns_max_iT2", 100000)
                proj.iteration.ns_converge_iT1 = _float(it_el, "ns_converge_iT1", 1e-8)
                proj.iteration.ns_converge_iT2 = _float(it_el, "ns_converge_iT2", 1e-6)
                proj.iteration.ns_update_interval = _int(it_el, "ns_update_interval", 1)
                proj.iteration.ade_max_iT = _int(it_el, "ade_max_iT", 50000)
                proj.iteration.ade_converge_iT = _float(it_el, "ade_converge_iT", 1e-8)
                proj.iteration.ade_update_interval = _int(it_el, "ade_update_interval", 1)

        # Chemistry
        chem = root.find("chemistry")
        if chem is not None:
            n_subs = _int(chem, "number_of_substrates", 0)
            for i in range(n_subs):
                se = chem.find(f"substrate{i}")
                if se is None:
                    continue
                s = Substrate()
                s.name = _text(se, "name_of_substrates", f"substrate{i}")
                s.initial_concentration = _float(se, "initial_concentration", 0.0)
                diff = se.find("substrate_diffusion_coefficients")
                if diff is not None:
                    s.diffusion_in_pore = _float(diff, "in_pore", 1e-9)
                    s.diffusion_in_biofilm = _float(diff, "in_biofilm", 2e-10)
                s.left_bc_type = _text(se, "left_boundary_type", "Dirichlet")
                s.right_bc_type = _text(se, "right_boundary_type", "Neumann")
                s.left_bc_value = _float(se, "left_boundary_condition", 0.0)
                s.right_bc_value = _float(se, "right_boundary_condition", 0.0)
                proj.substrates.append(s)

        # Microbiology
        micro = root.find("microbiology")
        if micro is not None:
            proj.microbiology.max_biomass_density = _float(micro, "maximum_biomass_density", 100.0)
            proj.microbiology.thrd_biofilm_fraction = _float(micro, "thrd_biofilm_fraction", 0.1)
            proj.microbiology.ca_method = _text(micro, "CA_method", "half")
            n_mic = _int(micro, "number_of_microbes", 0)
            for i in range(n_mic):
                me = micro.find(f"microbe{i}")
                if me is None:
                    continue
                m = Microbe()
                m.name = _text(me, "name_of_microbes", f"microbe{i}")
                m.solver_type = _text(me, "solver_type", "CA")
                m.reaction_type = _text(me, "reaction_type", "kinetics")
                m.initial_densities = _text(me, "initial_densities", "10.0 10.0")
                m.decay_coefficient = _float(me, "decay_coefficient", 1e-9)
                m.viscosity_ratio = _float(me, "viscosity_ratio_in_biofilm", 10.0)
                m.half_saturation_constants = _text(me, "half_saturation_constants", "")
                m.max_uptake_flux = _text(me, "maximum_uptake_flux", "")
                m.left_bc_type = _text(me, "left_boundary_type", "Neumann")
                m.right_bc_type = _text(me, "right_boundary_type", "Neumann")
                m.left_bc_value = _float(me, "left_boundary_condition", 0.0)
                m.right_bc_value = _float(me, "right_boundary_condition", 0.0)
                # Material numbers from domain
                mat_el = root.find(f".//material_numbers/microbe{i}")
                if mat_el is not None and mat_el.text:
                    m.material_numbers = mat_el.text.strip()
                proj.microbes.append(m)

        # Equilibrium
        eq_el = root.find("equilibrium")
        if eq_el is not None:
            proj.equilibrium.enabled = _bool(eq_el, "enabled", False)
            comp_el = eq_el.find("components")
            if comp_el is not None and comp_el.text:
                proj.equilibrium.components = comp_el.text.strip().split()
            stoich_el = eq_el.find("stoichiometry")
            if stoich_el is not None:
                for i in range(len(proj.substrates)):
                    sp = stoich_el.find(f"species{i}")
                    if sp is not None and sp.text:
                        row = [float(x) for x in sp.text.strip().split()]
                    else:
                        row = [0.0] * len(proj.equilibrium.components)
                    proj.equilibrium.stoichiometry.append(row)
            logk_el = eq_el.find("logK")
            if logk_el is not None:
                for i in range(len(proj.substrates)):
                    sp = logk_el.find(f"species{i}")
                    if sp is not None and sp.text:
                        proj.equilibrium.log_k.append(float(sp.text.strip()))
                    else:
                        proj.equilibrium.log_k.append(0.0)

        # IO
        io_el = root.find("IO")
        if io_el is not None:
            proj.io_settings.read_ns_file = _bool(io_el, "read_NS_file", False)
            proj.io_settings.read_ade_file = _bool(io_el, "read_ADE_file", False)
            proj.io_settings.ns_filename = _text(io_el, "ns_filename", "nsLattice")
            proj.io_settings.mask_filename = _text(io_el, "mask_filename", "maskLattice")
            proj.io_settings.subs_filename = _text(io_el, "subs_filename", "subsLattice")
            proj.io_settings.bio_filename = _text(io_el, "bio_filename", "bioLattice")
            proj.io_settings.save_vtk_interval = _int(io_el, "save_VTK_interval", 500)
            proj.io_settings.save_chk_interval = _int(io_el, "save_CHK_interval", 5000)

        proj.created = datetime.datetime.now().isoformat(timespec="seconds")
        proj.modified = proj.created
        return proj


def _text(parent, tag, default=""):
    el = parent.find(tag)
    if el is not None and el.text:
        return el.text.strip()
    return default


def _float(parent, tag, default=0.0):
    t = _text(parent, tag, "")
    if t:
        try:
            return float(t)
        except ValueError:
            pass
    return default


def _int(parent, tag, default=0):
    t = _text(parent, tag, "")
    if t:
        try:
            return int(t)
        except ValueError:
            try:
                return int(float(t))
            except ValueError:
                pass
    return default


def _bool(parent, tag, default=False):
    t = _text(parent, tag, "").lower()
    if t in ("true", "yes", "1"):
        return True
    if t in ("false", "no", "0"):
        return False
    return default


def _sci(value):
    """Format float in scientific notation where appropriate."""
    if value == 0.0:
        return "0.0"
    if abs(value) < 0.01 or abs(value) >= 1e6:
        return f"{value:.6e}"
    return str(value)


def _indent_xml(elem, level=0):
    """Add indentation to XML elements for pretty printing."""
    indent = "\n" + "    " * level
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = indent + "    "
        if not elem.tail or not elem.tail.strip():
            elem.tail = indent
        for child in elem:
            _indent_xml(child, level + 1)
        if not child.tail or not child.tail.strip():
            child.tail = indent
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = indent
    if level == 0:
        elem.tail = "\n"
