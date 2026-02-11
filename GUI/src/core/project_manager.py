"""Project save/load (.complab JSON) and XML import/export.

Produces XML that exactly matches what the C++ solver parses in
complab_functions.hh::initialize_complab().
"""

import json
import os
import datetime
import xml.etree.ElementTree as ET
from xml.dom import minidom
from pathlib import Path
from typing import Optional, Tuple

from .project import (
    CompLaBProject, PathSettings, SimulationMode, DomainSettings,
    FluidSettings, IterationSettings, Substrate, Microbe,
    MicrobiologySettings, EquilibriumSettings, IOSettings,
)


class ProjectManager:
    """Handles project file I/O: .complab (JSON) and CompLaB.xml."""

    # ── JSON project save/load ──────────────────────────────────────────

    @staticmethod
    def save_project(project: CompLaBProject, filepath: str) -> None:
        data = _project_to_dict(project)
        data["_meta"] = {
            "version": "2.0",
            "saved": datetime.datetime.now().isoformat(),
        }
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

    @staticmethod
    def load_project(filepath: str) -> CompLaBProject:
        with open(filepath, "r") as f:
            data = json.load(f)
        data.pop("_meta", None)
        return _dict_to_project(data)

    # ── XML export (CompLaB.xml) ────────────────────────────────────────

    @staticmethod
    def export_xml(project: CompLaBProject, filepath: str) -> None:
        root = ET.Element("parameters")

        # <path>
        path_el = ET.SubElement(root, "path")
        _add_text(path_el, "src_path", project.path_settings.src_path)
        _add_text(path_el, "input_path", project.path_settings.input_path)
        _add_text(path_el, "output_path", project.path_settings.output_path)

        # <simulation_mode>
        sm = project.simulation_mode
        sm_el = ET.SubElement(root, "simulation_mode")
        _add_text(sm_el, "biotic_mode", _bool_str(sm.biotic_mode))
        _add_text(sm_el, "enable_kinetics", _bool_str(sm.enable_kinetics))
        _add_text(sm_el, "enable_abiotic_kinetics",
                  _bool_str(sm.enable_abiotic_kinetics))
        _add_text(sm_el, "enable_validation_diagnostics",
                  _bool_str(sm.enable_validation_diagnostics))

        # <LB_numerics>
        lb = ET.SubElement(root, "LB_numerics")
        dom_el = ET.SubElement(lb, "domain")
        d = project.domain
        _add_text(dom_el, "nx", str(d.nx))
        _add_text(dom_el, "ny", str(d.ny))
        _add_text(dom_el, "nz", str(d.nz))
        _add_text(dom_el, "dx", _fmt_float(d.dx))
        if d.dy > 0 and d.dy != d.dx:
            _add_text(dom_el, "dy", _fmt_float(d.dy))
        if d.dz > 0 and d.dz != d.dx:
            _add_text(dom_el, "dz", _fmt_float(d.dz))
        _add_text(dom_el, "unit", d.unit)
        _add_text(dom_el, "characteristic_length", _fmt_float(d.characteristic_length))
        _add_text(dom_el, "filename", d.geometry_filename)

        mat_el = ET.SubElement(dom_el, "material_numbers")
        _add_text(mat_el, "pore", d.pore)
        _add_text(mat_el, "solid", d.solid)
        _add_text(mat_el, "bounce_back", d.bounce_back)
        # Per-microbe material numbers (only sessile/CA microbes)
        for i, mic in enumerate(project.microbiology.microbes):
            if mic.material_number.strip():
                _add_text(mat_el, f"microbe{i}", mic.material_number)

        fl = project.fluid
        _add_text(lb, "delta_P", _fmt_float(fl.delta_P))
        _add_text(lb, "Peclet", _fmt_float(fl.peclet))
        _add_text(lb, "tau", _fmt_float(fl.tau))
        _add_text(lb, "track_performance", _bool_str(fl.track_performance))

        it_el = ET.SubElement(lb, "iteration")
        it = project.iteration
        _add_text(it_el, "ns_max_iT1", str(it.ns_max_iT1))
        _add_text(it_el, "ns_max_iT2", str(it.ns_max_iT2))
        _add_text(it_el, "ns_converge_iT1", _fmt_float(it.ns_converge_iT1))
        _add_text(it_el, "ns_converge_iT2", _fmt_float(it.ns_converge_iT2))
        _add_text(it_el, "ade_max_iT", str(it.ade_max_iT))
        _add_text(it_el, "ade_converge_iT", _fmt_float(it.ade_converge_iT))
        if it.ns_rerun_iT0 > 0:
            _add_text(it_el, "ns_rerun_iT0", str(it.ns_rerun_iT0))
        if it.ade_rerun_iT0 > 0:
            _add_text(it_el, "ade_rerun_iT0", str(it.ade_rerun_iT0))
        _add_text(it_el, "ns_update_interval", str(it.ns_update_interval))
        _add_text(it_el, "ade_update_interval", str(it.ade_update_interval))

        # <chemistry>
        chem_el = ET.SubElement(root, "chemistry")
        subs = project.substrates
        _add_text(chem_el, "number_of_substrates", str(len(subs)))
        for i, s in enumerate(subs):
            s_el = ET.SubElement(chem_el, f"substrate{i}")
            _add_text(s_el, "name_of_substrates", s.name)
            _add_text(s_el, "initial_concentration", _fmt_float(s.initial_concentration))
            diff_el = ET.SubElement(s_el, "substrate_diffusion_coefficients")
            _add_text(diff_el, "in_pore", _fmt_float(s.diffusion_in_pore))
            _add_text(diff_el, "in_biofilm", _fmt_float(s.diffusion_in_biofilm))
            _add_text(s_el, "left_boundary_type", s.left_boundary_type)
            _add_text(s_el, "right_boundary_type", s.right_boundary_type)
            _add_text(s_el, "left_boundary_condition", _fmt_float(s.left_boundary_condition))
            _add_text(s_el, "right_boundary_condition", _fmt_float(s.right_boundary_condition))

        # <microbiology>
        mb = project.microbiology
        mb_el = ET.SubElement(root, "microbiology")
        microbes = mb.microbes
        _add_text(mb_el, "number_of_microbes", str(len(microbes)))
        _add_text(mb_el, "maximum_biomass_density", _fmt_float(mb.maximum_biomass_density))
        _add_text(mb_el, "thrd_biofilm_fraction", _fmt_float(mb.thrd_biofilm_fraction))
        _add_text(mb_el, "CA_method", mb.ca_method)
        for i, m in enumerate(microbes):
            m_el = ET.SubElement(mb_el, f"microbe{i}")
            _add_text(m_el, "name_of_microbes", m.name)
            _add_text(m_el, "solver_type", m.solver_type)
            _add_text(m_el, "reaction_type", m.reaction_type)
            _add_text(m_el, "initial_densities", m.initial_densities)
            _add_text(m_el, "decay_coefficient", _fmt_float(m.decay_coefficient))
            _add_text(m_el, "viscosity_ratio_in_biofilm",
                      _fmt_float(m.viscosity_ratio_in_biofilm))
            if m.half_saturation_constants.strip():
                _add_text(m_el, "half_saturation_constants", m.half_saturation_constants)
            if m.maximum_uptake_flux.strip():
                _add_text(m_el, "maximum_uptake_flux", m.maximum_uptake_flux)
            _add_text(m_el, "left_boundary_type", m.left_boundary_type)
            _add_text(m_el, "right_boundary_type", m.right_boundary_type)
            _add_text(m_el, "left_boundary_condition",
                      _fmt_float(m.left_boundary_condition))
            _add_text(m_el, "right_boundary_condition",
                      _fmt_float(m.right_boundary_condition))
            if m.biomass_diffusion_in_pore >= 0:
                bd_el = ET.SubElement(m_el, "biomass_diffusion_coefficients")
                _add_text(bd_el, "in_pore", _fmt_float(m.biomass_diffusion_in_pore))
                _add_text(bd_el, "in_biofilm", _fmt_float(m.biomass_diffusion_in_biofilm))

        # <equilibrium>
        eq = project.equilibrium
        eq_el = ET.SubElement(root, "equilibrium")
        _add_text(eq_el, "enabled", _bool_str(eq.enabled))
        if eq.enabled and eq.component_names:
            _add_text(eq_el, "components", " ".join(eq.component_names))
            # Solver parameters (read by C++ solver from XML)
            _add_text(eq_el, "max_iterations", str(eq.max_iterations))
            _add_text(eq_el, "tolerance", _fmt_float(eq.tolerance))
            _add_text(eq_el, "anderson_depth", str(eq.anderson_depth))
            _add_text(eq_el, "beta", _fmt_float(eq.beta))
            # stoichiometry
            st_el = ET.SubElement(eq_el, "stoichiometry")
            for i, row in enumerate(eq.stoichiometry):
                _add_text(st_el, f"species{i}", " ".join(_fmt_float(v) for v in row))
            # logK
            lk_el = ET.SubElement(eq_el, "logK")
            for i, val in enumerate(eq.log_k):
                _add_text(lk_el, f"species{i}", _fmt_float(val))

        # <IO>
        io = project.io_settings
        io_el = ET.SubElement(root, "IO")
        _add_text(io_el, "read_NS_file", _bool_str(io.read_ns_file))
        _add_text(io_el, "read_ADE_file", _bool_str(io.read_ade_file))
        _add_text(io_el, "ns_filename", io.ns_filename)
        _add_text(io_el, "mask_filename", io.mask_filename)
        _add_text(io_el, "subs_filename", io.subs_filename)
        _add_text(io_el, "bio_filename", io.bio_filename)
        _add_text(io_el, "save_VTK_interval", str(io.save_vtk_interval))
        _add_text(io_el, "save_CHK_interval", str(io.save_chk_interval))

        # Pretty-print
        rough = ET.tostring(root, encoding="unicode")
        parsed = minidom.parseString(rough)
        pretty = parsed.toprettyxml(indent="    ", encoding=None)
        # Remove extra XML declaration minidom adds
        lines = pretty.split("\n")
        if lines and lines[0].startswith("<?xml"):
            lines[0] = '<?xml version="1.0" ?>'
        with open(filepath, "w") as f:
            f.write("\n".join(lines))

    # ── XML import ──────────────────────────────────────────────────────

    @staticmethod
    def import_xml(filepath: str) -> CompLaBProject:
        tree = ET.parse(filepath)
        root = tree.getroot()
        proj = CompLaBProject()
        proj.name = Path(filepath).stem

        # <path>
        p = root.find("path")
        if p is not None:
            proj.path_settings.src_path = _get(p, "src_path", "src")
            proj.path_settings.input_path = _get(p, "input_path", "input")
            proj.path_settings.output_path = _get(p, "output_path", "output")

        # <simulation_mode>
        sm_el = root.find("simulation_mode")
        if sm_el is not None:
            proj.simulation_mode.biotic_mode = _get_bool(sm_el, "biotic_mode", True)
            proj.simulation_mode.enable_kinetics = _get_bool(sm_el, "enable_kinetics", True)
            proj.simulation_mode.enable_abiotic_kinetics = _get_bool(
                sm_el, "enable_abiotic_kinetics", False)
            proj.simulation_mode.enable_validation_diagnostics = _get_bool(
                sm_el, "enable_validation_diagnostics", False)

        # <LB_numerics>
        lb = root.find("LB_numerics")
        if lb is not None:
            dom = lb.find("domain")
            if dom is not None:
                proj.domain.nx = _get_int(dom, "nx", 50)
                proj.domain.ny = _get_int(dom, "ny", 30)
                proj.domain.nz = _get_int(dom, "nz", 30)
                proj.domain.dx = _get_float(dom, "dx", 1.0)
                proj.domain.dy = _get_float(dom, "dy", 0.0)
                proj.domain.dz = _get_float(dom, "dz", 0.0)
                proj.domain.unit = _get(dom, "unit", "um")
                proj.domain.characteristic_length = _get_float(
                    dom, "characteristic_length", 30.0)
                proj.domain.geometry_filename = _get(dom, "filename", "geometry.dat")
                mat = dom.find("material_numbers")
                if mat is not None:
                    proj.domain.pore = _get(mat, "pore", "2")
                    proj.domain.solid = _get(mat, "solid", "0")
                    proj.domain.bounce_back = _get(mat, "bounce_back", "1")

            proj.fluid.delta_P = _get_float(lb, "delta_P", 0.0)
            proj.fluid.peclet = _get_float(lb, "Peclet", 0.0)
            proj.fluid.tau = _get_float(lb, "tau", 0.8)
            proj.fluid.track_performance = _get_bool(lb, "track_performance", False)

            it = lb.find("iteration")
            if it is not None:
                proj.iteration.ns_max_iT1 = _get_int(it, "ns_max_iT1", 100000)
                proj.iteration.ns_max_iT2 = _get_int(it, "ns_max_iT2", 100000)
                proj.iteration.ns_converge_iT1 = _get_float(it, "ns_converge_iT1", 1e-8)
                proj.iteration.ns_converge_iT2 = _get_float(it, "ns_converge_iT2", 1e-6)
                proj.iteration.ade_max_iT = _get_int(it, "ade_max_iT", 50000)
                proj.iteration.ade_converge_iT = _get_float(it, "ade_converge_iT", 1e-8)
                proj.iteration.ns_rerun_iT0 = _get_int(it, "ns_rerun_iT0", 0)
                proj.iteration.ade_rerun_iT0 = _get_int(it, "ade_rerun_iT0", 0)
                proj.iteration.ns_update_interval = _get_int(it, "ns_update_interval", 1)
                proj.iteration.ade_update_interval = _get_int(it, "ade_update_interval", 1)

        # <chemistry>
        chem = root.find("chemistry")
        if chem is not None:
            n_subs = _get_int(chem, "number_of_substrates", 0)
            for i in range(n_subs):
                s_el = chem.find(f"substrate{i}")
                if s_el is None:
                    continue
                sub = Substrate()
                sub.name = _get(s_el, "name_of_substrates", f"substrate_{i}")
                sub.initial_concentration = _get_float(s_el, "initial_concentration", 0.0)
                diff = s_el.find("substrate_diffusion_coefficients")
                if diff is not None:
                    sub.diffusion_in_pore = _get_float(diff, "in_pore", 1e-9)
                    sub.diffusion_in_biofilm = _get_float(diff, "in_biofilm", 2e-10)
                sub.left_boundary_type = _get(s_el, "left_boundary_type", "Dirichlet")
                sub.right_boundary_type = _get(s_el, "right_boundary_type", "Neumann")
                sub.left_boundary_condition = _get_float(s_el, "left_boundary_condition", 0.0)
                sub.right_boundary_condition = _get_float(s_el, "right_boundary_condition", 0.0)
                proj.substrates.append(sub)

        # <microbiology>
        mb_el = root.find("microbiology")
        if mb_el is not None:
            proj.microbiology.maximum_biomass_density = _get_float(
                mb_el, "maximum_biomass_density", 100.0)
            proj.microbiology.thrd_biofilm_fraction = _get_float(
                mb_el, "thrd_biofilm_fraction", 0.1)
            proj.microbiology.ca_method = _get(mb_el, "CA_method", "fraction")
            n_mic = _get_int(mb_el, "number_of_microbes", 0)

            # Read material numbers from domain section
            mat_el = None
            if lb is not None:
                dom = lb.find("domain")
                if dom is not None:
                    mat_el = dom.find("material_numbers")

            for i in range(n_mic):
                m_el = mb_el.find(f"microbe{i}")
                if m_el is None:
                    continue
                mic = Microbe()
                mic.name = _get(m_el, "name_of_microbes", f"microbe_{i}")
                mic.solver_type = _get(m_el, "solver_type", "CA").upper()
                if mic.solver_type in ("CELLULAR AUTOMATA", "CELLULAR_AUTOMATA"):
                    mic.solver_type = "CA"
                elif mic.solver_type in ("LATTICE BOLTZMANN", "LB"):
                    mic.solver_type = "LBM"
                elif mic.solver_type in ("FINITE DIFFERENCE", "FINITE_DIFFERENCE"):
                    mic.solver_type = "FD"
                mic.reaction_type = _get(m_el, "reaction_type", "kinetics").lower()
                mic.initial_densities = _get(m_el, "initial_densities", "99.0")
                mic.decay_coefficient = _get_float(m_el, "decay_coefficient", 0.0)
                mic.viscosity_ratio_in_biofilm = _get_float(
                    m_el, "viscosity_ratio_in_biofilm", 10.0)
                mic.half_saturation_constants = _get(m_el, "half_saturation_constants", "")
                mic.maximum_uptake_flux = _get(m_el, "maximum_uptake_flux", "")
                mic.left_boundary_type = _get(m_el, "left_boundary_type", "Neumann")
                mic.right_boundary_type = _get(m_el, "right_boundary_type", "Neumann")
                mic.left_boundary_condition = _get_float(
                    m_el, "left_boundary_condition", 0.0)
                mic.right_boundary_condition = _get_float(
                    m_el, "right_boundary_condition", 0.0)
                bd = m_el.find("biomass_diffusion_coefficients")
                if bd is not None:
                    mic.biomass_diffusion_in_pore = _get_float(bd, "in_pore", -99.0)
                    mic.biomass_diffusion_in_biofilm = _get_float(bd, "in_biofilm", -99.0)
                # material number from domain section (only sessile microbes have this)
                if mat_el is not None:
                    mic.material_number = _get(mat_el, f"microbe{i}", "")
                proj.microbiology.microbes.append(mic)

        # <equilibrium>
        eq_el = root.find("equilibrium")
        if eq_el is not None:
            proj.equilibrium.enabled = _get_bool(eq_el, "enabled", False)
            comp_text = _get(eq_el, "components", "")
            if comp_text:
                proj.equilibrium.component_names = comp_text.split()
            # Solver parameters
            proj.equilibrium.max_iterations = _get_int(eq_el, "max_iterations", 200)
            proj.equilibrium.tolerance = _get_float(eq_el, "tolerance", 1e-8)
            proj.equilibrium.anderson_depth = _get_int(eq_el, "anderson_depth", 4)
            proj.equilibrium.beta = _get_float(eq_el, "beta", 1.0)
            st_el = eq_el.find("stoichiometry")
            if st_el is not None:
                n_subs = len(proj.substrates)
                for i in range(n_subs):
                    sp = st_el.find(f"species{i}")
                    if sp is not None and sp.text:
                        row = [float(x) for x in sp.text.strip().split()]
                    else:
                        row = [0.0] * len(proj.equilibrium.component_names)
                    proj.equilibrium.stoichiometry.append(row)
            lk_el = eq_el.find("logK")
            if lk_el is not None:
                n_subs = len(proj.substrates)
                for i in range(n_subs):
                    sp = lk_el.find(f"species{i}")
                    if sp is not None and sp.text:
                        proj.equilibrium.log_k.append(float(sp.text.strip()))
                    else:
                        proj.equilibrium.log_k.append(0.0)

        # <IO>
        io_el = root.find("IO")
        if io_el is not None:
            proj.io_settings.read_ns_file = _get_bool(io_el, "read_NS_file", False)
            proj.io_settings.read_ade_file = _get_bool(io_el, "read_ADE_file", False)
            proj.io_settings.ns_filename = _get(io_el, "ns_filename", "nsLattice")
            proj.io_settings.mask_filename = _get(io_el, "mask_filename", "maskLattice")
            proj.io_settings.subs_filename = _get(io_el, "subs_filename", "subsLattice")
            proj.io_settings.bio_filename = _get(io_el, "bio_filename", "bioLattice")
            proj.io_settings.save_vtk_interval = _get_int(io_el, "save_VTK_interval", 1000)
            proj.io_settings.save_chk_interval = _get_int(io_el, "save_CHK_interval", 1000000)

        return proj


# ── Helpers ─────────────────────────────────────────────────────────────

def _add_text(parent: ET.Element, tag: str, text: str) -> ET.Element:
    el = ET.SubElement(parent, tag)
    el.text = text
    return el


def _bool_str(val: bool) -> str:
    return "true" if val else "false"


def _fmt_float(val: float) -> str:
    if val == 0.0:
        return "0.0"
    if abs(val) >= 0.01 and abs(val) < 1e6:
        s = f"{val:.10g}"
    else:
        s = f"{val:.6e}"
    return s


def _get(el: ET.Element, tag: str, default: str) -> str:
    child = el.find(tag)
    if child is not None and child.text:
        return child.text.strip()
    return default


def _get_int(el: ET.Element, tag: str, default: int) -> int:
    try:
        return int(_get(el, tag, str(default)))
    except ValueError:
        return default


def _get_float(el: ET.Element, tag: str, default: float) -> float:
    try:
        return float(_get(el, tag, str(default)))
    except ValueError:
        return default


def _get_bool(el: ET.Element, tag: str, default: bool) -> bool:
    val = _get(el, tag, "").lower()
    if val in ("true", "yes", "1", "biotic"):
        return True
    if val in ("false", "no", "0", "abiotic"):
        return False
    return default


def _project_to_dict(proj: CompLaBProject) -> dict:
    """Serialize project to a JSON-friendly dict."""
    from dataclasses import asdict
    return asdict(proj)


def _dict_to_project(d: dict) -> CompLaBProject:
    """Deserialize project from a dict."""
    proj = CompLaBProject()
    proj.name = d.get("name", "Untitled")

    if "path_settings" in d:
        ps = d["path_settings"]
        proj.path_settings = PathSettings(**ps)

    if "simulation_mode" in d:
        proj.simulation_mode = SimulationMode(**d["simulation_mode"])

    if "domain" in d:
        proj.domain = DomainSettings(**d["domain"])

    if "fluid" in d:
        proj.fluid = FluidSettings(**d["fluid"])

    if "iteration" in d:
        proj.iteration = IterationSettings(**d["iteration"])

    if "substrates" in d:
        proj.substrates = [Substrate(**s) for s in d["substrates"]]

    if "microbiology" in d:
        mb = d["microbiology"]
        microbes = [Microbe(**m) for m in mb.pop("microbes", [])]
        proj.microbiology = MicrobiologySettings(**mb)
        proj.microbiology.microbes = microbes

    if "equilibrium" in d:
        proj.equilibrium = EquilibriumSettings(**d["equilibrium"])

    if "io_settings" in d:
        proj.io_settings = IOSettings(**d["io_settings"])

    return proj
