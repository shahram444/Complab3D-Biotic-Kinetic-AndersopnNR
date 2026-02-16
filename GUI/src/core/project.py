"""CompLaB3D project data model - exact match to C++ solver XML parameters."""

from dataclasses import dataclass, field
from typing import List
import copy


@dataclass
class PathSettings:
    """<path> section of CompLaB.xml."""
    src_path: str = "src"
    input_path: str = "input"
    output_path: str = "output"


@dataclass
class SimulationMode:
    """<simulation_mode> section."""
    biotic_mode: bool = True
    enable_kinetics: bool = True
    enable_abiotic_kinetics: bool = False
    enable_validation_diagnostics: bool = False


@dataclass
class DomainSettings:
    """<LB_numerics><domain> section.

    Note: C++ solver adds +2 to nx internally for ghost boundary nodes.
    The GUI stores the user-facing value (what goes into XML).
    dy/dz default to dx if set to 0.
    """
    nx: int = 50
    ny: int = 30
    nz: int = 30
    dx: float = 1.0
    dy: float = 0.0
    dz: float = 0.0
    unit: str = "um"
    characteristic_length: float = 30.0
    geometry_filename: str = "geometry.dat"
    pore: str = "2"
    solid: str = "0"
    bounce_back: str = "1"


@dataclass
class FluidSettings:
    """<LB_numerics> flow parameters."""
    delta_P: float = 2.0e-3
    peclet: float = 1.0
    tau: float = 0.8
    track_performance: bool = False


@dataclass
class IterationSettings:
    """<LB_numerics><iteration> section."""
    ns_max_iT1: int = 100000
    ns_max_iT2: int = 100000
    ns_converge_iT1: float = 1e-8
    ns_converge_iT2: float = 1e-6
    ade_max_iT: int = 10000000
    ade_converge_iT: float = 1e-8
    ns_rerun_iT0: int = 0
    ade_rerun_iT0: int = 0
    ns_update_interval: int = 1
    ade_update_interval: int = 1


@dataclass
class Substrate:
    """Single substrate in <chemistry><substrate{i}> section."""
    name: str = "substrate_0"
    initial_concentration: float = 0.0
    diffusion_in_pore: float = 1e-9
    diffusion_in_biofilm: float = 2e-10
    left_boundary_type: str = "Dirichlet"
    right_boundary_type: str = "Neumann"
    left_boundary_condition: float = 0.0
    right_boundary_condition: float = 0.0


@dataclass
class Microbe:
    """Single microbe in <microbiology><microbe{i}> section.

    material_number: space-separated integers, e.g. "3" or "3 6" for core+fringe.
    initial_densities: space-separated floats, must match material_number count.
    half_saturation_constants / maximum_uptake_flux: space-separated floats,
        length must equal number of substrates.
    """
    name: str = "microbe_0"
    solver_type: str = "CA"
    reaction_type: str = "kinetics"
    material_number: str = ""
    initial_densities: str = "99.0"
    decay_coefficient: float = 0.0
    viscosity_ratio_in_biofilm: float = 10.0
    half_saturation_constants: str = ""
    maximum_uptake_flux: str = ""
    left_boundary_type: str = "Neumann"
    right_boundary_type: str = "Neumann"
    left_boundary_condition: float = 0.0
    right_boundary_condition: float = 0.0
    biomass_diffusion_in_pore: float = -99.0
    biomass_diffusion_in_biofilm: float = -99.0


@dataclass
class MicrobiologySettings:
    """<microbiology> global settings + microbe list."""
    maximum_biomass_density: float = 100.0
    thrd_biofilm_fraction: float = 0.1
    ca_method: str = "fraction"
    microbes: List[Microbe] = field(default_factory=list)


@dataclass
class EquilibriumSettings:
    """<equilibrium> section.

    stoichiometry: 2D list [species_index][component_index].
    log_k: list of floats, one per species (substrate).
    Solver parameters match C++ defaults in complab3d_processors_part4_eqsolver.hh.
    """
    enabled: bool = False
    component_names: List[str] = field(default_factory=list)
    stoichiometry: List[List[float]] = field(default_factory=list)
    log_k: List[float] = field(default_factory=list)
    max_iterations: int = 200
    tolerance: float = 1e-10
    anderson_depth: int = 4
    beta: float = 1.0


@dataclass
class IOSettings:
    """<IO> section."""
    read_ns_file: bool = False
    read_ade_file: bool = False
    ns_filename: str = "nsLattice"
    mask_filename: str = "maskLattice"
    subs_filename: str = "subsLattice"
    bio_filename: str = "bioLattice"
    save_vtk_interval: int = 1000
    save_chk_interval: int = 1000000


@dataclass
class CompLaBProject:
    """Root project data model, maps 1:1 to CompLaB.xml structure."""
    name: str = "Untitled"
    path_settings: PathSettings = field(default_factory=PathSettings)
    simulation_mode: SimulationMode = field(default_factory=SimulationMode)
    domain: DomainSettings = field(default_factory=DomainSettings)
    fluid: FluidSettings = field(default_factory=FluidSettings)
    iteration: IterationSettings = field(default_factory=IterationSettings)
    substrates: List[Substrate] = field(default_factory=list)
    microbiology: MicrobiologySettings = field(default_factory=MicrobiologySettings)
    equilibrium: EquilibriumSettings = field(default_factory=EquilibriumSettings)
    io_settings: IOSettings = field(default_factory=IOSettings)
    # Kinetics .hh source code (deployed alongside CompLaB.xml on export)
    template_key: str = ""
    kinetics_source: str = ""
    abiotic_kinetics_source: str = ""

    def deep_copy(self) -> "CompLaBProject":
        return copy.deepcopy(self)

    def validate(self) -> List[str]:
        """Comprehensive validation against C++ solver expectations.

        Checks every aspect of the XML that the GUI generates:
        domain, chemistry, microbiology, solver, I/O, equilibrium,
        cross-references, and consistency.
        """
        errors = []
        warnings = []
        num_subs = len(self.substrates)

        # ── 1. Path settings ────────────────────────────────────────
        ps = self.path_settings
        if not ps.src_path:
            errors.append("[Path] src_path is empty.")
        if not ps.input_path:
            errors.append("[Path] input_path is empty.")
        if not ps.output_path:
            errors.append("[Path] output_path is empty.")

        # ── 2. Simulation mode consistency ──────────────────────────
        sm = self.simulation_mode
        if not sm.biotic_mode and sm.enable_kinetics:
            errors.append(
                "[Mode] enable_kinetics=true but biotic_mode=false. "
                "Kinetics requires biotic_mode=true (for Monod kinetics). "
                "Use enable_abiotic_kinetics for abiotic reactions.")
        if not sm.biotic_mode and len(self.microbiology.microbes) > 0:
            errors.append(
                "[Mode] biotic_mode=false but microbes are defined. "
                "Set biotic_mode=true or remove microbes.")

        # Flow-only: no substrates is fine (solver only runs NS)
        # Diffusion-only: Pe=0 is fine (pure diffusion, no advection)

        # Warn about abiotic kinetics with zero substrate concentrations
        if sm.enable_abiotic_kinetics and len(self.substrates) > 0:
            all_zero = all(
                s.initial_concentration == 0.0
                and s.left_boundary_condition == 0.0
                and s.right_boundary_condition == 0.0
                for s in self.substrates
            )
            if all_zero:
                errors.append(
                    "[Mode] Abiotic kinetics is enabled but all substrate "
                    "concentrations and boundary conditions are zero. "
                    "Reactions need non-zero concentrations to produce "
                    "meaningful results. Set a non-zero inlet concentration "
                    "or initial concentration, or switch to 'Transport only' "
                    "mode if no reactions are needed.")

        # ── 3. Domain settings ──────────────────────────────────────
        d = self.domain
        if d.nx < 1 or d.ny < 1 or d.nz < 1:
            errors.append("[Domain] Dimensions (nx, ny, nz) must be >= 1.")
        if d.nx < 3:
            errors.append(
                "[Domain] nx must be >= 3 (need at least inlet + 1 cell + outlet).")
        if d.dx <= 0:
            errors.append("[Domain] Grid spacing dx must be > 0.")
        if d.dy < 0:
            errors.append("[Domain] Grid spacing dy cannot be negative.")
        if d.dz < 0:
            errors.append("[Domain] Grid spacing dz cannot be negative.")
        if d.unit not in ("m", "mm", "um"):
            errors.append("[Domain] Unit must be 'm', 'mm', or 'um'.")
        if not d.geometry_filename:
            errors.append("[Domain] Geometry filename is required.")
        elif not d.geometry_filename.endswith(".dat"):
            errors.append("[Domain] Geometry file must be a .dat file.")

        # Material numbers (pore can be space-separated, e.g. "2 4")
        try:
            pore_vals = [int(x) for x in d.pore.strip().split()]
            solid_val = int(d.solid)
            bb_val = int(d.bounce_back)
            mat_set = set(pore_vals) | {solid_val, bb_val}
            if solid_val in pore_vals or bb_val in pore_vals or solid_val == bb_val:
                errors.append(
                    f"[Domain] Material numbers must be distinct: "
                    f"pore={d.pore}, solid={solid_val}, bounce_back={bb_val}.")
        except ValueError:
            errors.append(
                "[Domain] Material numbers (pore, solid, bounce_back) "
                "must be space-separated integers.")

        # Characteristic length for Peclet
        fl = self.fluid
        if fl.peclet > 0 and d.characteristic_length <= 0:
            errors.append(
                "[Domain] characteristic_length must be > 0 when Peclet > 0.")

        # ── 4. Fluid / LBM settings ────────────────────────────────
        if fl.tau <= 0.5:
            errors.append(
                "[Solver] Relaxation time tau must be > 0.5 for LBM stability.")
        if fl.tau > 2.0:
            errors.append(
                "[Solver] tau > 2.0 is numerically unstable. "
                "Recommended range: 0.5 < tau < 2.0.")
        if fl.delta_P < 0:
            errors.append("[Solver] Pressure gradient delta_P cannot be negative.")
        if fl.peclet < 0:
            errors.append("[Solver] Peclet number cannot be negative.")

        # ── 5. Iteration settings ───────────────────────────────────
        it = self.iteration
        if it.ns_max_iT1 < 100:
            errors.append("[Iteration] ns_max_iT1 should be >= 100.")
        if it.ns_max_iT2 < 100:
            errors.append("[Iteration] ns_max_iT2 should be >= 100.")
        if it.ade_max_iT < 100 and num_subs > 0:
            errors.append("[Iteration] ade_max_iT should be >= 100.")
        if it.ns_converge_iT1 <= 0:
            errors.append("[Iteration] NS convergence (phase 1) must be > 0.")
        if it.ns_converge_iT2 <= 0:
            errors.append("[Iteration] NS convergence (phase 2) must be > 0.")
        if it.ade_converge_iT <= 0:
            errors.append("[Iteration] ADE convergence must be > 0.")
        if it.ns_update_interval < 1:
            errors.append("[Iteration] NS update interval must be >= 1.")
        if it.ade_update_interval < 1:
            errors.append("[Iteration] ADE update interval must be >= 1.")

        # ── 6. Chemistry / Substrates ───────────────────────────────
        sub_names = set()
        for i, s in enumerate(self.substrates):
            prefix = f"[Substrate {i} '{s.name}']"
            if not s.name or not s.name.strip():
                errors.append(f"[Substrate {i}] Name is empty.")
            elif s.name in sub_names:
                errors.append(f"{prefix} Duplicate substrate name.")
            else:
                sub_names.add(s.name)

            if s.initial_concentration < 0:
                errors.append(f"{prefix} Initial concentration cannot be negative.")
            if s.diffusion_in_pore <= 0:
                errors.append(
                    f"{prefix} Diffusion coefficient in pore must be > 0.")
            if s.diffusion_in_biofilm < 0:
                errors.append(
                    f"{prefix} Diffusion coefficient in biofilm cannot be negative.")
            if s.diffusion_in_biofilm > s.diffusion_in_pore:
                errors.append(
                    f"{prefix} Biofilm diffusion ({s.diffusion_in_biofilm}) should be "
                    f"<= pore diffusion ({s.diffusion_in_pore}).")
            if s.left_boundary_type not in ("Dirichlet", "Neumann"):
                errors.append(
                    f"{prefix} Left BC type must be 'Dirichlet' or 'Neumann' "
                    f"(got '{s.left_boundary_type}').")
            if s.right_boundary_type not in ("Dirichlet", "Neumann"):
                errors.append(
                    f"{prefix} Right BC type must be 'Dirichlet' or 'Neumann' "
                    f"(got '{s.right_boundary_type}').")
            if s.left_boundary_type == "Dirichlet" and s.left_boundary_condition < 0:
                errors.append(
                    f"{prefix} Left Dirichlet BC value cannot be negative.")
            if s.right_boundary_type == "Dirichlet" and s.right_boundary_condition < 0:
                errors.append(
                    f"{prefix} Right Dirichlet BC value cannot be negative.")

        # ── 7. Microbiology ─────────────────────────────────────────
        if sm.biotic_mode:
            microbes = self.microbiology.microbes
            if len(microbes) == 0:
                errors.append(
                    "[Microbiology] biotic_mode=true but no microbes defined.")

            mic_names = set()
            used_mat_numbers = set()
            try:
                for p in d.pore.strip().split():
                    used_mat_numbers.add(int(p))
                used_mat_numbers.add(int(d.solid))
                used_mat_numbers.add(int(d.bounce_back))
            except ValueError:
                pass

            for i, m in enumerate(microbes):
                prefix = f"[Microbe {i} '{m.name}']"
                if not m.name or not m.name.strip():
                    errors.append(f"[Microbe {i}] Name is empty.")
                elif m.name in mic_names:
                    errors.append(f"{prefix} Duplicate microbe name.")
                else:
                    mic_names.add(m.name)

                if m.solver_type not in ("CA", "LBM", "FD"):
                    errors.append(
                        f"{prefix} Solver type must be 'CA', 'LBM', or 'FD' "
                        f"(got '{m.solver_type}').")

                if m.reaction_type not in ("kinetics", "kns", "none", "no", "0", ""):
                    errors.append(
                        f"{prefix} Reaction type must be 'kinetics' or 'none' "
                        f"(got '{m.reaction_type}').")

                # Material number validation
                if m.solver_type == "CA":
                    if not m.material_number.strip():
                        errors.append(
                            f"{prefix} CA solver requires material_number(s) "
                            f"(e.g., '3' or '3 6').")
                    else:
                        mat_nums = m.material_number.strip().split()
                        init_dens = m.initial_densities.strip().split()
                        if len(mat_nums) != len(init_dens):
                            errors.append(
                                f"{prefix} material_number count ({len(mat_nums)}) "
                                f"must match initial_densities count ({len(init_dens)}).")
                        for mn_str in mat_nums:
                            try:
                                mn = int(mn_str)
                                if mn in used_mat_numbers:
                                    errors.append(
                                        f"{prefix} Material number {mn} conflicts "
                                        f"with another material assignment.")
                                used_mat_numbers.add(mn)
                            except ValueError:
                                errors.append(
                                    f"{prefix} Material number '{mn_str}' is not an integer.")

                    if self.microbiology.maximum_biomass_density <= 0:
                        errors.append(
                            f"{prefix} CA solver requires positive maximum_biomass_density.")
                    if m.viscosity_ratio_in_biofilm <= 0:
                        errors.append(
                            f"{prefix} CA solver requires positive viscosity_ratio_in_biofilm.")

                if m.solver_type == "FD":
                    if m.biomass_diffusion_in_pore < 0:
                        errors.append(
                            f"{prefix} FD solver requires biomass_diffusion_in_pore >= 0.")
                    if m.biomass_diffusion_in_biofilm < 0:
                        errors.append(
                            f"{prefix} FD solver requires biomass_diffusion_in_biofilm >= 0.")

                # Initial densities must be valid numbers
                for val_str in m.initial_densities.strip().split():
                    try:
                        val = float(val_str)
                        if val < 0:
                            errors.append(
                                f"{prefix} initial_density '{val_str}' is negative.")
                    except ValueError:
                        errors.append(
                            f"{prefix} initial_density '{val_str}' is not a number.")

                if m.decay_coefficient < 0:
                    errors.append(f"{prefix} decay_coefficient cannot be negative.")

                # Half-saturation constants must match substrate count
                if num_subs > 0:
                    if m.half_saturation_constants.strip():
                        ks_vals = m.half_saturation_constants.strip().split()
                        if len(ks_vals) != num_subs:
                            errors.append(
                                f"{prefix} half_saturation_constants has {len(ks_vals)} "
                                f"values but there are {num_subs} substrates.")
                        for ks_str in ks_vals:
                            try:
                                float(ks_str)
                            except ValueError:
                                errors.append(
                                    f"{prefix} half_saturation_constants value "
                                    f"'{ks_str}' is not a number.")

                    if m.maximum_uptake_flux.strip():
                        vmax_vals = m.maximum_uptake_flux.strip().split()
                        if len(vmax_vals) != num_subs:
                            errors.append(
                                f"{prefix} maximum_uptake_flux has {len(vmax_vals)} "
                                f"values but there are {num_subs} substrates.")
                        for vmax_str in vmax_vals:
                            try:
                                float(vmax_str)
                            except ValueError:
                                errors.append(
                                    f"{prefix} maximum_uptake_flux value "
                                    f"'{vmax_str}' is not a number.")

                # Microbe boundary conditions
                if m.left_boundary_type not in ("Dirichlet", "Neumann"):
                    errors.append(
                        f"{prefix} Left BC must be 'Dirichlet' or 'Neumann'.")
                if m.right_boundary_type not in ("Dirichlet", "Neumann"):
                    errors.append(
                        f"{prefix} Right BC must be 'Dirichlet' or 'Neumann'.")

            # CA method check
            ca_method = self.microbiology.ca_method.lower()
            if ca_method not in ("half", "fraction"):
                errors.append(
                    f"[Microbiology] CA_method must be 'half' or 'fraction' "
                    f"(got '{self.microbiology.ca_method}').")

            # Biofilm fraction threshold
            bft = self.microbiology.thrd_biofilm_fraction
            if bft < 0 or bft > 1:
                errors.append(
                    f"[Microbiology] thrd_biofilm_fraction must be in [0, 1] "
                    f"(got {bft}).")

        # ── 8. Abiotic kinetics ─────────────────────────────────────
        if sm.enable_abiotic_kinetics:
            if num_subs < 1:
                errors.append(
                    "[Mode] Abiotic kinetics requires at least one substrate.")

        # ── 9. Equilibrium solver ───────────────────────────────────
        eq = self.equilibrium
        if eq.enabled:
            if not eq.component_names:
                errors.append(
                    "[Equilibrium] Enabled but no component species defined.")
            if num_subs < 1:
                errors.append(
                    "[Equilibrium] Requires at least one substrate.")
            n_comp = len(eq.component_names)

            # Stoichiometry matrix
            if len(eq.stoichiometry) != num_subs:
                errors.append(
                    f"[Equilibrium] Stoichiometry has {len(eq.stoichiometry)} rows "
                    f"but there are {num_subs} substrates.")
            for i, row in enumerate(eq.stoichiometry):
                if len(row) != n_comp:
                    errors.append(
                        f"[Equilibrium] Stoichiometry row {i} has {len(row)} columns "
                        f"but there are {n_comp} components.")

            # logK values
            if len(eq.log_k) != num_subs:
                errors.append(
                    f"[Equilibrium] logK has {len(eq.log_k)} entries "
                    f"but there are {num_subs} substrates.")

            # Solver parameters
            if eq.max_iterations < 1:
                errors.append("[Equilibrium] max_iterations must be >= 1.")
            if eq.tolerance <= 0:
                errors.append("[Equilibrium] tolerance must be > 0.")
            if eq.anderson_depth < 0:
                errors.append("[Equilibrium] anderson_depth must be >= 0.")
            if eq.beta <= 0 or eq.beta > 2:
                errors.append(
                    "[Equilibrium] beta (relaxation) should be in (0, 2].")

        # ── 10. I/O settings ───────────────────────────────────────
        io = self.io_settings
        if io.save_vtk_interval < 1:
            errors.append("[IO] VTK save interval must be >= 1.")
        if io.save_chk_interval < 1:
            errors.append("[IO] Checkpoint save interval must be >= 1.")
        if io.save_vtk_interval > it.ade_max_iT:
            errors.append(
                f"[IO] VTK save interval ({io.save_vtk_interval}) is larger than "
                f"max ADE iterations ({it.ade_max_iT}). No VTK files will be saved.")

        # ── 11. Cross-checks ───────────────────────────────────────
        # No substrates with kinetics enabled (flow-only with 0 substrates is OK)
        if num_subs == 0 and sm.enable_kinetics:
            errors.append(
                "[Cross-check] Biotic kinetics enabled but no substrates defined.")
        if num_subs == 0 and sm.enable_abiotic_kinetics:
            errors.append(
                "[Cross-check] Abiotic kinetics enabled but no substrates defined.")

        # All Neumann BCs on all substrates (no source) - might not reach steady state
        if num_subs > 0:
            all_neumann = all(
                s.left_boundary_type == "Neumann" and
                s.right_boundary_type == "Neumann" and
                s.initial_concentration == 0.0
                for s in self.substrates)
            if all_neumann and not sm.enable_abiotic_kinetics:
                errors.append(
                    "[Cross-check] All substrates have Neumann BCs and zero initial "
                    "concentration. No substrate source exists - simulation will have "
                    "zero concentrations everywhere.")

        # ── 12. Kinetics .hh cross-validation ─────────────────────────
        from .kinetics_templates import validate_kinetics_vs_project
        num_mic = len(self.microbiology.microbes)
        kin_errors = validate_kinetics_vs_project(
            biotic_source=self.kinetics_source,
            abiotic_source=self.abiotic_kinetics_source,
            num_substrates=num_subs,
            num_microbes=num_mic,
            biotic_mode=sm.biotic_mode,
            enable_kinetics=sm.enable_kinetics,
            enable_abiotic=sm.enable_abiotic_kinetics,
        )
        errors.extend(kin_errors)

        # ── 13. Template key vs current mode consistency ──────────────
        from .kinetics_templates import get_kinetics_info
        if self.template_key:
            tinfo = get_kinetics_info(self.template_key)
            if tinfo:
                if tinfo.needs_biotic and not sm.biotic_mode:
                    errors.append(
                        f"[Template] Template '{self.template_key}' requires "
                        f"biotic_mode=true but it is currently false. "
                        f"The defineKinetics.hh code expects microbes.")
                if tinfo.needs_biotic and not sm.enable_kinetics:
                    errors.append(
                        f"[Template] Template '{self.template_key}' requires "
                        f"enable_kinetics=true but it is currently false.")
                if tinfo.needs_abiotic and not sm.enable_abiotic_kinetics:
                    errors.append(
                        f"[Template] Template '{self.template_key}' requires "
                        f"enable_abiotic_kinetics=true but it is currently false.")
                # Check substrate count vs template expectations
                if tinfo.biotic_substrate_indices:
                    needed = max(tinfo.biotic_substrate_indices) + 1
                    if num_subs < needed:
                        errors.append(
                            f"[Template] Template '{self.template_key}' "
                            f"needs at least {needed} substrate(s) "
                            f"(uses C[{max(tinfo.biotic_substrate_indices)}]) "
                            f"but only {num_subs} defined.")
                if tinfo.abiotic_substrate_indices:
                    needed = max(tinfo.abiotic_substrate_indices) + 1
                    if num_subs < needed:
                        errors.append(
                            f"[Template] Template '{self.template_key}' "
                            f"needs at least {needed} substrate(s) "
                            f"(uses C[{max(tinfo.abiotic_substrate_indices)}]) "
                            f"but only {num_subs} defined.")
                if tinfo.biotic_microbe_indices:
                    needed = max(tinfo.biotic_microbe_indices) + 1
                    if num_mic < needed:
                        errors.append(
                            f"[Template] Template '{self.template_key}' "
                            f"needs at least {needed} microbe(s) "
                            f"(uses B[{max(tinfo.biotic_microbe_indices)}]) "
                            f"but only {num_mic} defined.")

        return errors

    def validate_files(self, work_dir: str) -> List[str]:
        """File-system validation: geometry file, on-disk .hh files.

        *work_dir* is the project directory (where CompLaB.xml lives).
        This checks that actual files on disk match the project config.
        """
        import os
        errors: List[str] = []
        if not work_dir or not os.path.isdir(work_dir):
            return errors

        sm = self.simulation_mode
        d = self.domain
        num_subs = len(self.substrates)
        num_mic = len(self.microbiology.microbes)

        # ── Geometry file ─────────────────────────────────────────────
        input_dir = os.path.join(work_dir, self.path_settings.input_path)
        geom_path = os.path.join(input_dir, d.geometry_filename)
        # Also check directly in work_dir
        geom_alt = os.path.join(work_dir, d.geometry_filename)

        found_geom = None
        if os.path.isfile(geom_path):
            found_geom = geom_path
        elif os.path.isfile(geom_alt):
            found_geom = geom_alt

        if found_geom is None:
            # Only warn if this is not a flow-only run (flow-only doesn't need geometry)
            if num_subs > 0 or sm.biotic_mode:
                errors.append(
                    f"[Geometry] File not found: '{d.geometry_filename}'\n"
                    f"  Searched: {geom_path}\n"
                    f"           {geom_alt}\n"
                    f"  The solver needs this file. Generate it with "
                    f"Tools > Geometry Generator.")
        else:
            # Check file size vs nx*ny*nz
            try:
                file_size = os.path.getsize(found_geom)
                expected = d.nx * d.ny * d.nz
                if file_size != expected:
                    ratio = file_size / expected if expected > 0 else 0
                    errors.append(
                        f"[Geometry] SIZE MISMATCH: {d.geometry_filename} has "
                        f"{file_size:,} bytes but nx*ny*nz = "
                        f"{d.nx}*{d.ny}*{d.nz} = {expected:,}.\n"
                        f"  Ratio: {ratio:.2f}x (file is "
                        f"{'too large' if file_size > expected else 'too small'}).\n"
                        f"  This is the #1 cause of heap corruption crashes!\n"
                        f"  Fix: change nx/ny/nz to match the file, or "
                        f"regenerate geometry.dat with correct dimensions.")
            except OSError as e:
                errors.append(
                    f"[Geometry] Cannot read '{found_geom}': {e}")

        # ── On-disk .hh files ─────────────────────────────────────────
        if sm.enable_kinetics and sm.biotic_mode:
            biotic_path = os.path.join(work_dir, "defineKinetics.hh")
            if not os.path.isfile(biotic_path):
                errors.append(
                    f"[Kinetics] defineKinetics.hh not found in {work_dir}.\n"
                    f"  Biotic kinetics is enabled - the solver needs this file.\n"
                    f"  Export CompLaB.xml to deploy it, or use "
                    f"Tools > Kinetics Editor to create one.")

        if sm.enable_abiotic_kinetics:
            abiotic_path = os.path.join(work_dir, "defineAbioticKinetics.hh")
            if not os.path.isfile(abiotic_path):
                errors.append(
                    f"[Kinetics] defineAbioticKinetics.hh not found in "
                    f"{work_dir}.\n"
                    f"  Abiotic kinetics is enabled - the solver needs this "
                    f"file.\n  Export CompLaB.xml to deploy it, or use "
                    f"Tools > Kinetics Editor to create one.")

        # ── On-disk XML consistency check ────────────────────────────
        xml_path = os.path.join(work_dir, "CompLaB.xml")
        if os.path.isfile(xml_path):
            try:
                import xml.etree.ElementTree as ET
                tree = ET.parse(xml_path)
                root = tree.getroot()

                # Check substrate count
                chem = root.find("chemistry")
                if chem is not None:
                    xml_nsubs_el = chem.find("number_of_substrates")
                    if xml_nsubs_el is not None and xml_nsubs_el.text:
                        xml_nsubs = int(xml_nsubs_el.text.strip())
                        if xml_nsubs != num_subs:
                            errors.append(
                                f"[XML Sync] On-disk CompLaB.xml has "
                                f"number_of_substrates={xml_nsubs} but GUI "
                                f"has {num_subs}. Re-export XML before running.")

                # Check microbe count
                mb = root.find("microbiology")
                if mb is not None:
                    xml_nmic_el = mb.find("number_of_microbes")
                    if xml_nmic_el is not None and xml_nmic_el.text:
                        xml_nmic = int(xml_nmic_el.text.strip())
                        if xml_nmic != num_mic:
                            errors.append(
                                f"[XML Sync] On-disk CompLaB.xml has "
                                f"number_of_microbes={xml_nmic} but GUI "
                                f"has {num_mic}. Re-export XML before running.")

                # Check domain dimensions
                lb = root.find("LB_numerics")
                if lb is not None:
                    dom = lb.find("domain")
                    if dom is not None:
                        for dim_name in ("nx", "ny", "nz"):
                            dim_el = dom.find(dim_name)
                            if dim_el is not None and dim_el.text:
                                xml_val = int(dim_el.text.strip())
                                gui_val = getattr(d, dim_name)
                                if xml_val != gui_val:
                                    errors.append(
                                        f"[XML Sync] On-disk CompLaB.xml has "
                                        f"{dim_name}={xml_val} but GUI has "
                                        f"{gui_val}. Re-export XML before "
                                        f"running.")
            except Exception:
                pass  # XML parsing failed - not critical for validation

        return errors
