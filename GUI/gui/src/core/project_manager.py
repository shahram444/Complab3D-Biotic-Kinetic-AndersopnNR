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
    MicrobeDistribution, DistributionType
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
            print(f"Project saved to: {project.path}")
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
            inp = path_elem.find("input_path")
            if inp is not None:
                project.input_path = inp.text.strip()
            out = path_elem.find("output_path")
            if out is not None:
                project.output_path = out.text.strip()
                
        # Parse LB numerics
        lb_elem = root.find("LB_numerics")
        if lb_elem is not None:
            # Fluid settings
            delta_p = lb_elem.find("delta_P")
            if delta_p is not None:
                project.fluid.delta_p = float(delta_p.text.strip())
            peclet = lb_elem.find("Peclet")
            if peclet is not None:
                project.fluid.peclet = float(peclet.text.strip())
            tau = lb_elem.find("tau")
            if tau is not None:
                project.fluid.tau = float(tau.text.strip())
                
            # Domain settings
            domain_elem = lb_elem.find("domain")
            if domain_elem is not None:
                filename = domain_elem.find("filename")
                if filename is not None:
                    project.domain.geometry_file = filename.text.strip()
                nx = domain_elem.find("nx")
                if nx is not None:
                    project.domain.nx = int(nx.text.strip())
                ny = domain_elem.find("ny")
                if ny is not None:
                    project.domain.ny = int(ny.text.strip())
                nz = domain_elem.find("nz")
                if nz is not None:
                    project.domain.nz = int(nz.text.strip())
                dx = domain_elem.find("dx")
                if dx is not None:
                    project.domain.dx = float(dx.text.strip())
                    project.domain.dy = project.domain.dx
                    project.domain.dz = project.domain.dx
                    
        return project
        
    def export_to_xml(self, project: CompLaBProject, xml_path: str):
        """Export project to CompLaB XML format"""
        root = ET.Element("parameters")
        
        # Path section
        path_elem = ET.SubElement(root, "path")
        ET.SubElement(path_elem, "input_path").text = f" {project.input_path} "
        ET.SubElement(path_elem, "output_path").text = f" {project.output_path} "
        
        # LB_numerics section
        lb_elem = ET.SubElement(root, "LB_numerics")
        ET.SubElement(lb_elem, "delta_P").text = f" {project.fluid.delta_p} "
        ET.SubElement(lb_elem, "Peclet").text = f" {project.fluid.peclet} "
        ET.SubElement(lb_elem, "tau").text = f" {project.fluid.tau} "
        
        # Domain
        domain_elem = ET.SubElement(lb_elem, "domain")
        ET.SubElement(domain_elem, "filename").text = f" {project.domain.geometry_file} "
        ET.SubElement(domain_elem, "nx").text = f" {project.domain.nx} "
        ET.SubElement(domain_elem, "ny").text = f" {project.domain.ny} "
        ET.SubElement(domain_elem, "nz").text = f" {project.domain.nz} "
        ET.SubElement(domain_elem, "dx").text = f" {project.domain.dx} "
        ET.SubElement(domain_elem, "characteristic_length").text = f" {project.domain.characteristic_length} "
        ET.SubElement(domain_elem, "unit").text = f" {project.domain.unit} "
        
        # Material numbers
        mat_elem = ET.SubElement(domain_elem, "material_numbers")
        ET.SubElement(mat_elem, "pore").text = f" {project.domain.pore_material} "
        ET.SubElement(mat_elem, "solid").text = f" {project.domain.solid_material} "
        ET.SubElement(mat_elem, "bounce_back").text = f" {project.domain.bounce_back_material} "
        
        # Add microbe material numbers
        for i, microbe in enumerate(project.microbes):
            ET.SubElement(mat_elem, f"microbe{i}").text = f" {microbe.material_number} "
            
        ET.SubElement(lb_elem, "track_performance").text = " yes " if project.io.track_performance else " no "
        
        # Iteration settings
        iter_elem = ET.SubElement(lb_elem, "iteration")
        ET.SubElement(iter_elem, "ns_rerun_iT0").text = f" {project.iterations.ns_rerun_iT0} "
        ET.SubElement(iter_elem, "ns_max_iT1").text = f" {project.iterations.ns_max_iT1} "
        ET.SubElement(iter_elem, "ns_converge_iT1").text = f" {project.iterations.ns_converge_iT1} "
        ET.SubElement(iter_elem, "ns_update_interval").text = f" {project.iterations.ns_update_interval} "
        ET.SubElement(iter_elem, "ns_max_iT2").text = f" {project.iterations.ns_max_iT2} "
        ET.SubElement(iter_elem, "ns_converge_iT2").text = f" {project.iterations.ns_converge_iT2} "
        ET.SubElement(iter_elem, "ade_rerun_iT0").text = f" {project.iterations.ade_rerun_iT0} "
        ET.SubElement(iter_elem, "ade_max_iT").text = f" {project.iterations.ade_max_iT} "
        ET.SubElement(iter_elem, "ade_converge_iT").text = f" {project.iterations.ade_converge_iT} "
        ET.SubElement(iter_elem, "ade_update_interval").text = f" {project.iterations.ade_update_interval} "
        
        # Chemistry section - ALWAYS write (even if empty)
        chem_elem = ET.SubElement(root, "chemistry")
        ET.SubElement(chem_elem, "number_of_substrates").text = f" {len(project.substrates)} "
        
        for i, substrate in enumerate(project.substrates):
            sub_elem = ET.SubElement(chem_elem, f"substrate{i}")
            ET.SubElement(sub_elem, "name_of_substrates").text = f" {substrate.name} "
            
            diff_elem = ET.SubElement(sub_elem, "substrate_diffusion_coefficients")
            ET.SubElement(diff_elem, "in_pore").text = f" {substrate.diffusion_coefficients.in_pore} "
            ET.SubElement(diff_elem, "in_biofilm").text = f" {substrate.diffusion_coefficients.in_biofilm} "
            
            ET.SubElement(sub_elem, "initial_concentration").text = f" {substrate.initial_concentration} "
            
            ET.SubElement(sub_elem, "left_boundary_type").text = f" {substrate.left_boundary.bc_type.value} "
            ET.SubElement(sub_elem, "left_boundary_condition").text = f" {substrate.left_boundary.value} "
            ET.SubElement(sub_elem, "right_boundary_type").text = f" {substrate.right_boundary.bc_type.value} "
            ET.SubElement(sub_elem, "right_boundary_condition").text = f" {substrate.right_boundary.value} "
        
        # Microbiology section - ALWAYS write (required by CompLaB C++)
        bio_elem = ET.SubElement(root, "microbiology")
        ET.SubElement(bio_elem, "number_of_microbes").text = f" {len(project.microbes)} "
        
        for i, microbe in enumerate(project.microbes):
            mic_elem = ET.SubElement(bio_elem, f"microbe{i}")
            ET.SubElement(mic_elem, "name_of_microbes").text = f" {microbe.name} "
            ET.SubElement(mic_elem, "solver_type").text = f" {microbe.solver_type.value} "
            ET.SubElement(mic_elem, "initial_densities").text = " " + " ".join(str(d) for d in microbe.initial_densities) + " "
            
            diff_elem = ET.SubElement(mic_elem, "biomass_diffusion_coefficients")
            ET.SubElement(diff_elem, "in_pore").text = f" {microbe.diffusion_coefficients.in_pore} "
            ET.SubElement(diff_elem, "in_biofilm").text = f" {microbe.diffusion_coefficients.in_biofilm} "
            
            ET.SubElement(mic_elem, "viscosity_ratio_in_biofilm").text = f" {microbe.viscosity_ratio_in_biofilm} "
            
            ET.SubElement(mic_elem, "left_boundary_type").text = f" {microbe.left_boundary.bc_type.value} "
            ET.SubElement(mic_elem, "left_boundary_condition").text = f" {microbe.left_boundary.value} "
            ET.SubElement(mic_elem, "right_boundary_type").text = f" {microbe.right_boundary.bc_type.value} "
            ET.SubElement(mic_elem, "right_boundary_condition").text = f" {microbe.right_boundary.value} "
            
            ET.SubElement(mic_elem, "decay_coefficient").text = f" {microbe.decay_coefficient} "
            ET.SubElement(mic_elem, "half_saturation_constants").text = " " + " ".join(str(k) for k in microbe.half_saturation_constants) + " "
            ET.SubElement(mic_elem, "maximum_uptake_flux").text = " " + " ".join(str(v) for v in microbe.maximum_uptake_flux) + " "
            
        # Always write these microbiology settings (even with 0 microbes)
        ET.SubElement(bio_elem, "maximum_biomass_density").text = f" {project.microbiology.maximum_biomass_density} "
        ET.SubElement(bio_elem, "thrd_biofilm_fraction").text = f" {project.microbiology.thrd_biofilm_fraction} "
        ET.SubElement(bio_elem, "CA_method").text = f" {project.microbiology.ca_method} "
        
        # IO section
        io_elem = ET.SubElement(root, "IO")
        ET.SubElement(io_elem, "read_NS_file").text = " yes " if project.io.read_ns_file else " no "
        ET.SubElement(io_elem, "read_ADE_file").text = " yes " if project.io.read_ade_file else " no "
        ET.SubElement(io_elem, "ns_filename").text = f" {project.io.ns_filename} "
        ET.SubElement(io_elem, "mask_filename").text = f" {project.io.mask_filename} "
        ET.SubElement(io_elem, "subs_filename").text = f" {project.io.subs_filename} "
        ET.SubElement(io_elem, "bio_filename").text = f" {project.io.bio_filename} "
        ET.SubElement(io_elem, "save_VTK_interval").text = f" {project.io.save_vtk_interval} "
        ET.SubElement(io_elem, "save_CHK_interval").text = f" {project.io.save_chk_interval} "
        
        # Write XML with proper formatting
        xml_str = minidom.parseString(ET.tostring(root)).toprettyxml(indent="    ")
        
        # Remove extra blank lines
        lines = [line for line in xml_str.split('\n') if line.strip()]
        xml_str = '\n'.join(lines)
        
        with open(xml_path, 'w') as f:
            f.write(xml_str)
            
        print(f"XML exported to: {xml_path}")
