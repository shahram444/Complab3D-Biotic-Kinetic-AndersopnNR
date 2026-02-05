/* ============================================================================
 * CompLaB3D - Three-Dimensional Biogeochemical Reactive Transport Solver
 * ============================================================================
 *
 * Author:      Shahram Asgari
 * Advisor:     Dr. Christof Meile
 * Laboratory:  Meile Lab
 * Institution: University of Georgia (UGA)
 *
 * ============================================================================
 * CALCULATION FLOW (10 PHASES):
 * ───────────────────────────────────────────────────────────────────────────
 * PHASE 1:  Load XML configuration and validate inputs
 * PHASE 2:  Geometry setup and preprocessing
 * PHASE 3:  Navier-Stokes flow field simulation
 *           └─ STEP 3.1: Initial pressure simulation → measure u₀
 *           └─ STEP 3.2: Calculate permeability: k = (u₀ × ν × L) / ΔP₀
 *           └─ STEP 3.3: Calculate target velocity: u_target = (Pe × D) / L
 *           └─ STEP 3.4: Corrected pressure: ΔP_new = (u_target × ν × L) / k
 *           └─ STEP 3.5: Second NS simulation → achieve target velocity
 *           └─ STEP 3.6: Stability checks (Ma, CFL, τ)
 * PHASE 4:  Reactive transport lattice setup (substrates + biomass)
 * PHASE 5:  NS-ADE velocity field coupling
 * PHASE 6:  Main simulation loop
 *           └─ STEP 6.1: Collision step (LBM)
 *           └─ STEP 6.2: Kinetics reactions (Monod, decay)
 *           └─ STEP 6.3: Equilibrium chemistry solver
 *           └─ STEP 6.4: Biomass expansion (CA/FD)
 *           └─ STEP 6.5: Flow field update (if biofilm changed)
 *           └─ STEP 6.6: Streaming step (LBM)
 * PHASE 7:  Output VTI/CHK files
 * PHASE 8:  Calculate moments and BTC analysis
 * PHASE 9:  Write summary files
 * PHASE 10: Finalize and cleanup
 * ───────────────────────────────────────────────────────────────────────────
 *
 * SIMULATION MODES:
 *   - biotic_mode: true/false (with/without microbes)
 *   - enable_kinetics: true/false (kinetics reactions on/off)
 *   - enable_validation_diagnostics: true/false (detailed per-iteration output)
 *
 * OUTPUT FILES:
 *   - VTI: Concentration, biomass, velocity fields
 *   - CHK: Binary checkpoints for restart
 *   - CSV: BTC timeseries, domain properties, moments summary
 *
 * ============================================================================
 */

#include "complab_functions.hh"
#include "complab3d_processors.hh"
#include "../defineKinetics.hh"  // For KineticsStats namespace - in project root

#include <chrono>
#include <string>
#include <iostream>
#include <cstring>
#include <vector>
#include <sys/stat.h>
#include <iomanip>
#include <cmath>

// ============================================================================
// STABILITY CHECK STRUCTURE  
// ============================================================================
struct StabilityReport {
    T Ma, CFL, tau_NS, tau_ADE, Pe_grid;
    bool Ma_ok, Ma_warning, CFL_ok, tau_NS_ok, tau_ADE_ok, Pe_grid_ok, all_ok, has_warnings;
};

StabilityReport performStabilityChecks(T u_max, T tau_NS, T tau_ADE, T D_lattice) {
    StabilityReport report;
    T cs = std::sqrt(1.0 / 3.0);
    report.Ma = u_max / cs;
    report.Ma_ok = (report.Ma < 1.0);
    report.Ma_warning = (report.Ma > 0.3);
    report.CFL = u_max;
    report.CFL_ok = (report.CFL < 1.0);
    report.tau_NS = tau_NS;
    report.tau_NS_ok = (tau_NS > 0.5 && tau_NS < 2.0);
    report.tau_ADE = tau_ADE;
    report.tau_ADE_ok = (tau_ADE > 0.5 && tau_ADE < 2.0);
    report.Pe_grid = (D_lattice > 1e-14) ? (u_max / D_lattice) : 0.0;
    report.Pe_grid_ok = (report.Pe_grid < 2.0);
    report.all_ok = report.Ma_ok && report.CFL_ok && report.tau_NS_ok && report.tau_ADE_ok;
    report.has_warnings = report.Ma_warning || !report.Pe_grid_ok;
    return report;
}

void printStabilityReport(const StabilityReport& report) {
    pcout << "\n╔════════════════════════════════════════════════════════════╗\n";
    pcout << "║              STABILITY CHECK REPORT                        ║\n";
    pcout << "╠════════════════════════════════════════════════════════════╣\n";
    pcout << "║ Ma = " << std::setprecision(4) << report.Ma << (report.Ma_ok ? " OK" : " FAIL");
    pcout << "   CFL = " << report.CFL << (report.CFL_ok ? " OK" : " FAIL") << "             ║\n";
    pcout << "║ tau_NS = " << report.tau_NS << (report.tau_NS_ok ? " OK" : " FAIL");
    pcout << "   tau_ADE = " << report.tau_ADE << (report.tau_ADE_ok ? " OK" : " FAIL") << "            ║\n";
    pcout << "║ Pe_grid = " << report.Pe_grid << (report.Pe_grid_ok ? " OK" : " WARN") << "                                       ║\n";
    pcout << "╚════════════════════════════════════════════════════════════╝\n\n";
}


int main(int argc, char **argv) {

    plbInit(&argc, &argv);
    global::timer("total").start();

    // ════════════════════════════════════════════════════════════════════════════
    // STARTUP BANNER
    // ════════════════════════════════════════════════════════════════════════════
    pcout << "\n";
    pcout << "╔══════════════════════════════════════════════════════════════════════════╗\n";
    pcout << "║                            CompLaB3D                                     ║\n";
    pcout << "║       Three-Dimensional Biogeochemical Reactive Transport Solver        ║\n";
    pcout << "║              Lattice Boltzmann Method (LBM) + Equilibrium                ║\n";
    pcout << "╠══════════════════════════════════════════════════════════════════════════╣\n";
    pcout << "║  Author:  Shahram Asgari                                                 ║\n";
    pcout << "║  Advisor: Dr. Christof Meile                                             ║\n";
    pcout << "║  Lab:     Meile Lab, University of Georgia                               ║\n";
    pcout << "╚══════════════════════════════════════════════════════════════════════════╝\n\n";

    ImageWriter<T> image("leeloo");

    // Diagnostic counters
    plint diag_ca_triggers = 0;
    plint diag_ca_redistributions = 0;
    T diag_initial_biomass = 0.0;

    // asserted variables
    plint kns_count=0, fd_count=0, lb_count=0, ca_count=0, bfilm_count=0, bfree_count=0;
    char *main_path = (char*)malloc(100 * sizeof(char));
    getcwd(main_path, 100 * sizeof(char));
    char *src_path = (char*)malloc(100 * sizeof(char));
    char *input_path = (char*)malloc(100 * sizeof(char));
    char *output_path = (char*)malloc(100 * sizeof(char));
    char *ns_filename = (char*)malloc(100 * sizeof(char));
    plint nx, ny, nz, num_of_microbes, num_of_substrates;
    T dx, dy, dz, deltaP, Pe, charcs_length;
    std::string geom_filename, mask_filename;
    std::vector<bool> vec_left_btype, vec_right_btype, bio_left_btype, bio_right_btype;
    std::vector<T> vec_c0, vec_b0_free, vec_left_bcondition, vec_right_bcondition, bio_left_bcondition, bio_right_bcondition, vec_permRatio;
    std::vector< std::vector<T> > vec_b0_all, vec_b0_film, vec_Kc_kns, vec_Vmax, vec_Vmax_kns;
    std::vector<T> vec_mu;
    std::vector< std::vector<T> > vec_Kc;

    // variables with default values
    std::string ade_filename, bio_filename;
    bool read_NS_file=0, read_ADE_file=0, soluteDindex=0, bmassDindex=0, track_performance=0., halfflag=0;
    plint no_dynamics=0, bounce_back=1, ns_rerun_iT0=0, ns_update_interval=1, ade_update_interval=1,
        ns_maxiTer_1, ns_maxiTer_2, ade_rerun_iT0=0, ade_maxiTer=10000000, ade_VTI_iTer=1000, ade_CHK_iTer=1000000;
    T tau=0.8, max_bMassRho=1., ns_converge_iT1=1e-8, ns_converge_iT2=1e-4, ade_converge_iT=1e-8, thrd_bFilmFrac;

    T DarcyOutletUx=0., permeability=0., u_target=0., deltaP_new=0., u_final=0., Pe_achieved=0.;
    T tau_ADE_fixed=0.8, D_lattice_fixed=0., tortuosity_factor=3.0, safety_factor=1.5;
    plint estimated_iterations=0;

    std::vector<bool> bmass_type;
    std::vector<plint> pore_dynamics, solver_type, reaction_type;
    std::vector<T> vec_solute_poreD, vec_solute_bFilmD, vec_bMass_poreD, vec_bMass_bFilmD, vec_mu_kns;
    std::vector<std::string> vec_subs_names, vec_microbes_names;
    std::vector< std::vector<plint> > bio_dynamics;

    // Equilibrium chemistry variables
    bool useEquilibrium = false;
    EquilibriumChemistry<T> eqSolver;
    T eqtime = 0.0;
    std::vector<std::string> eq_component_names;
    std::vector<T> eq_logK_values;
    std::vector<std::vector<T>> eq_stoich_matrix;

    // Biotic/Abiotic and Kinetics control
    bool biotic_mode = true;      // true = with microbes, false = abiotic transport only
    bool enable_kinetics = true;  // true = kinetics enabled, false = equilibrium only
    bool enable_validation_diagnostics = false;  // true = detailed per-iteration diagnostics

    std::string str_mainDir=main_path;
    if (std::to_string(str_mainDir.back()).compare("/")!=0) { str_mainDir+="/"; }
    std::srand(std::time(nullptr));

    // ════════════════════════════════════════════════════════════════════════════
    // PHASE 1: LOAD CONFIGURATION
    // ════════════════════════════════════════════════════════════════════════════
    pcout << "┌────────────────────────────────────────────────────────────────────────┐\n";
    pcout << "│ PHASE 1: LOADING CONFIGURATION                                        │\n";
    pcout << "└────────────────────────────────────────────────────────────────────────┘\n";
    
    int erck = 0;
    try {
        erck=initialize_complab( main_path, src_path, input_path, output_path, ns_filename, ade_filename, bio_filename, geom_filename, mask_filename,
        read_NS_file, ns_rerun_iT0, ns_converge_iT1, ns_converge_iT2, ns_maxiTer_1, ns_maxiTer_2, ns_update_interval, ade_update_interval,
        read_ADE_file, ade_rerun_iT0, ade_VTI_iTer, ade_CHK_iTer, ade_converge_iT, ade_maxiTer, nx, ny, nz, dx, dy, dz, deltaP, tau,
        Pe, charcs_length, vec_solute_poreD, vec_solute_bFilmD, vec_bMass_poreD, vec_bMass_bFilmD, soluteDindex, bmassDindex, thrd_bFilmFrac, vec_permRatio, max_bMassRho,
        pore_dynamics, bounce_back, no_dynamics, bio_dynamics, num_of_microbes, num_of_substrates, vec_subs_names, vec_microbes_names,
        solver_type, fd_count, lb_count, ca_count, bfilm_count, bfree_count, kns_count, reaction_type,
        vec_c0, vec_left_btype, vec_right_btype, vec_left_bcondition, vec_right_bcondition, vec_b0_all, bio_left_btype, bio_right_btype, bio_left_bcondition, bio_right_bcondition,
        vec_Kc, vec_Kc_kns, vec_mu, vec_mu_kns, bmass_type, vec_b0_free, vec_b0_film, vec_Vmax, vec_Vmax_kns, track_performance, halfflag,
        useEquilibrium, eq_component_names, eq_logK_values, eq_stoich_matrix,
        biotic_mode, enable_kinetics,
        enable_validation_diagnostics);
    }
    catch (PlbIOException& exception) {
        pcout << "  [ERROR] " << exception.what() << "\n";
        return -1;
    }
    if (erck!=0) { return -1; }
    pcout << "  [OK] XML configuration loaded and validated\n";

    plint rxn_count = kns_count;

    // ════════════════════════════════════════════════════════════════════════════
    // PRINT CONFIGURATION SUMMARY
    // ════════════════════════════════════════════════════════════════════════════
    pcout << "\n┌────────────────────────────────────────────────────────────────────────┐\n";
    pcout << "│ CONFIGURATION SUMMARY                                                 │\n";
    pcout << "├────────────────────────────────────────────────────────────────────────┤\n";
    pcout << "│ Domain: " << nx << " x " << ny << " x " << nz << " = " << nx*ny*nz << " voxels\n";
    pcout << "│ Resolution: dx = " << std::scientific << dx << " m\n";
    pcout << "│ Peclet: " << std::fixed << Pe << "\n";
    pcout << "├────────────────────────────────────────────────────────────────────────┤\n";
    pcout << "│ SUBSTRATES (" << num_of_substrates << "):\n";
    for (plint iS = 0; iS < num_of_substrates; ++iS) {
        pcout << "│   [" << iS << "] " << vec_subs_names[iS] << "  C0=" << std::scientific << vec_c0[iS] << " M\n";
    }
    pcout << "├────────────────────────────────────────────────────────────────────────┤\n";
    pcout << "│ MICROBES (" << num_of_microbes << "):\n";
    for (plint iM = 0; iM < num_of_microbes; ++iM) {
        pcout << "│   [" << iM << "] " << vec_microbes_names[iM];
        pcout << " type=" << (bmass_type[iM] ? "biofilm" : "planktonic");
        pcout << " solver=" << (solver_type[iM]==1 ? "FD" : (solver_type[iM]==2 ? "CA" : "LBM"));
        pcout << " rxn=" << (reaction_type[iM]==1 ? "kinetics" : "none") << "\n";
    }
    pcout << "├────────────────────────────────────────────────────────────────────────┤\n";
    pcout << "│ SOLVERS ENABLED:\n";
    pcout << "│   [" << (kns_count > 0 ? "X" : " ") << "] Kinetics      - " << kns_count << " model(s)\n";
    pcout << "│   [" << (useEquilibrium ? "X" : " ") << "] Equilibrium   - " << eq_component_names.size() << " component(s)\n";
    pcout << "│   [" << (ca_count > 0 ? "X" : " ") << "] CA            - " << ca_count << " microbe(s)\n";
    pcout << "│   [" << (fd_count > 0 ? "X" : " ") << "] FD            - " << fd_count << " microbe(s)\n";
    pcout << "│   [" << (lb_count > 0 ? "X" : " ") << "] LB Diffusion  - " << lb_count << " microbe(s)\n";
    pcout << "├────────────────────────────────────────────────────────────────────────┤\n";
    pcout << "│ BIOMASS: Bmax=" << max_bMassRho << " kg/m3, threshold=" << thrd_bFilmFrac << "\n";
    pcout << "│ SIMULATION: max_iter=" << ade_maxiTer << ", VTI=" << ade_VTI_iTer << ", CHK=" << ade_CHK_iTer << "\n";
    pcout << "└────────────────────────────────────────────────────────────────────────┘\n\n";

    // Equilibrium setup
    if (useEquilibrium) {
        pcout << "  [EQ] Setting up equilibrium chemistry solver...\n";
        eqSolver.setSpeciesNames(vec_subs_names);
        if (!eq_component_names.empty()) eqSolver.setComponentNames(eq_component_names);
        if (!eq_stoich_matrix.empty()) eqSolver.setStoichiometryMatrix(eq_stoich_matrix);
        if (!eq_logK_values.empty()) eqSolver.setLogK(eq_logK_values);
        eqSolver.setMaxIterations(200);
        eqSolver.setTolerance(1e-10);
        eqSolver.setAndersonDepth(4);
        pcout << "  [EQ] Solver configured: Anderson+PCF, tol=1e-10, maxiter=200\n\n";
    }

    std::string str_inputDir=input_path, str_outputDir=output_path;
    if (std::to_string(str_inputDir.back()).compare("/")!=0) { str_inputDir+="/"; }
    if (std::to_string(str_outputDir.back()).compare("/")!=0) { str_outputDir+="/"; }

    // ════════════════════════════════════════════════════════════════════════════
    // PHASE 2: GEOMETRY AND FLOW SETUP
    // ════════════════════════════════════════════════════════════════════════════
    struct stat statStruct;
    stat(output_path, &statStruct);

    pcout << "┌────────────────────────────────────────────────────────────────────────┐\n";
    pcout << "│ PHASE 2: GEOMETRY AND FLOW SETUP                                      │\n";
    pcout << "└────────────────────────────────────────────────────────────────────────┘\n";
    pcout << "  Main:   " << str_mainDir << "\n";
    pcout << "  Input:  " << main_path << "/" << input_path << "\n";
    pcout << "  Output: " << main_path << "/" << output_path << "\n";
    
    if (S_ISDIR(statStruct.st_mode)) {} else { mkdir(output_path, 0777); }
    global::directories().setOutputDir(str_outputDir);

    T PoreMeanU=0, PoreMaxUx=0;
    plint iT = 0;
    T nsLatticeTau = tau;
    T nsLatticeOmega = 1 / nsLatticeTau;
    T nsLatticeNu = NSDES<T>::cs2*(nsLatticeTau-0.5);
    char *ns_read_filename = strcat(strdup(str_inputDir.c_str()),ns_filename);

    pcout << "  [GEOM] Reading " << geom_filename << "...\n";
    MultiScalarField3D<int> geometry(nx,ny,nz);
    readGeometry(str_inputDir+geom_filename, geometry);
    saveGeometry("inputGeom", geometry);
    pcout << "  [GEOM] Geometry loaded\n";

    MultiScalarField3D<int> distanceDomain(nx,ny,nz);
    distanceDomain = geometry;
    std::vector< std::vector< std::vector<plint> > > distVec(nx);
    for (plint iX=0; iX<nx; ++iX) {
        distVec[iX]=std::vector< std::vector<plint> > (ny);
        for (plint iY=0; iY<ny; ++iY) { distVec[iX][iY]=std::vector<plint> (nz); }
    }
    calculateDistanceFromSolid(distanceDomain, no_dynamics, bounce_back, distVec);
    applyProcessingFunctional(new createDistanceDomain3D<int> (distVec), distanceDomain.getBoundingBox(), distanceDomain);

    MultiScalarField3D<int> ageDomain(nx,ny,nz);
    ageDomain = geometry;
    applyProcessingFunctional(new createAgeDomain3D<int> (pore_dynamics, bounce_back, no_dynamics), ageDomain.getBoundingBox(), ageDomain);
    pcout << "  [GEOM] Distance and age fields ready\n";
    
    if (track_performance == 1) { pcout << "  [PERF] Performance tracking ON - VTI disabled\n"; }

    pcout << "  [NS] Initializing fluid lattice (deltaP=" << deltaP << ")...\n";
    MultiBlockLattice3D<T,NSDES> nsLattice(nx, ny, nz, new IncBGKdynamics<T,NSDES>(nsLatticeOmega));
    util::ValueTracer<T> ns_convg1(1.0,1000.0,ns_converge_iT1);
    NSdomainSetup(nsLattice, createLocalBoundaryCondition3D<T,NSDES>(), geometry, deltaP, nsLatticeOmega, pore_dynamics, bounce_back, no_dynamics, bio_dynamics, vec_permRatio);

    // NS main loop
    global::timer("NS").start();
    if (Pe == 0) { pcout << "  [NS] Pe=0, skipping flow solver\n"; }
    else {
        pcout << "  [NS] tau=" << nsLatticeTau << ", omega=" << nsLatticeOmega << ", nu=" << nsLatticeNu << "\n";
        if (read_NS_file == 1 && track_performance == 0) {
            pcout << "  [NS] Loading checkpoint...\n";
            try { loadBinaryBlock(nsLattice, strcat(ns_read_filename,".chk")); }
            catch (PlbIOException& exception) { pcout << "  [NS] ERROR: " << exception.what() << "\n"; return -1; }
            if (ns_rerun_iT0 > 0) {
                iT = ns_rerun_iT0;
                for (; iT < ns_maxiTer_1; ++iT) {
                    nsLattice.collideAndStream();
                    ns_convg1.takeValue(getStoredAverageEnergy(nsLattice),true);
                    if (ns_convg1.hasConverged()) break;
                }
            }
        }
        else {
            pcout << "  [NS] Running new simulation...\n";
            for (; iT < ns_maxiTer_1; ++iT) {
                nsLattice.collideAndStream();
                ns_convg1.takeValue(getStoredAverageEnergy(nsLattice),true);
                if (ns_convg1.hasConverged()) break;
            }
        }
        pcout << "  [NS] Converged at iter=" << iT << "\n";

        // Calculate velocities
        if (bfilm_count > 0) {
            plint totalCount = 0; T totalVel = 0;
            for (size_t iT = 0; iT < pore_dynamics.size(); ++iT) {
                plint poreCount = MaskedScalarCounts3D(Box3D(1,nx-2,0,ny-1,0,nz-1), geometry, pore_dynamics[iT]);
                totalCount += poreCount;
                totalVel += computeAverage(*computeVelocityNorm(nsLattice, Box3D(1,nx-2,0,ny-1,0,nz-1)), geometry, pore_dynamics[iT]) * poreCount;
            }
            for (plint iT0 = 0; iT0 < bfilm_count; ++iT0) {
                plint bFilmCount = 0;
                for (size_t iT1 = 0; iT1 < bio_dynamics[iT0].size(); ++iT1) {
                    bFilmCount += MaskedScalarCounts3D(Box3D(1,nx-2,0,ny-1,0,nz-1), geometry, bio_dynamics[iT0][iT1]);
                }
                totalCount += bFilmCount;
                totalVel += computeAverage(*computeVelocityNorm(nsLattice, Box3D(1,nx-2,0,ny-1,0,nz-1)), geometry, bio_dynamics[iT0][0]) * bFilmCount;
            }
            PoreMeanU = totalVel / totalCount;
        }
        else { PoreMeanU = computeAverage(*computeVelocityNorm(nsLattice, Box3D(1,nx-2,0,ny-1,0,nz-1))); }

        PoreMaxUx = computeMax(*computeVelocityComponent(nsLattice, Box3D(1,nx-2,0,ny-1,0,nz-1), 0));
        DarcyOutletUx = computeAverage(*computeVelocityComponent(nsLattice, Box3D(nx-2,nx-2, 0,ny-1, 0,nz-1), 0));
        
        D_lattice_fixed = RXNDES<T>::cs2 * (tau_ADE_fixed - 0.5);
        permeability = DarcyOutletUx * nsLatticeNu * charcs_length / deltaP;
        pcout << "  [NS] Permeability k=" << permeability << " (lattice)\n";
        
        u_target = Pe * D_lattice_fixed / charcs_length;
        deltaP_new = u_target * nsLatticeNu * charcs_length / permeability;
        
        if (std::abs(deltaP_new - deltaP) / deltaP > 0.01) {
            pcout << "  [NS] Re-running with corrected deltaP=" << deltaP_new << "\n";
            NSdomainSetup(nsLattice, createLocalBoundaryCondition3D<T,NSDES>(), geometry, deltaP_new, nsLatticeOmega, pore_dynamics, bounce_back, no_dynamics, bio_dynamics, vec_permRatio);
            ns_convg1.resetValues();
            for (plint iT2 = 0; iT2 < ns_maxiTer_1; ++iT2) {
                nsLattice.collideAndStream();
                ns_convg1.takeValue(getStoredAverageEnergy(nsLattice), true);
                if (ns_convg1.hasConverged()) break;
            }
            PoreMeanU = computeAverage(*computeVelocityNorm(nsLattice, Box3D(1,nx-2,0,ny-1,0,nz-1)));
            PoreMaxUx = computeMax(*computeVelocityComponent(nsLattice, Box3D(1,nx-2,0,ny-1,0,nz-1), 0));
            DarcyOutletUx = computeAverage(*computeVelocityComponent(nsLattice, Box3D(nx-2,nx-2,0,ny-1,0,nz-1), 0));
            deltaP = deltaP_new;
        }
        
        u_final = DarcyOutletUx;
        Pe_achieved = u_final * charcs_length / D_lattice_fixed;
        pcout << "  [NS] Pe achieved=" << Pe_achieved << " (target=" << Pe << ")\n";
        
        StabilityReport stability = performStabilityChecks(PoreMaxUx, nsLatticeTau, tau_ADE_fixed, D_lattice_fixed);
        printStabilityReport(stability);

        T Ma = PoreMaxUx/sqrt(RXNDES<T>::cs2);
        if (Ma > 1) { pcout << "  [NS] ERROR: Ma=" << Ma << " > 1\n"; return -1; }
    }
    global::timer("NS").stop();
    T nstime = global::timer("NS").getTime();

    if (ade_maxiTer == 0) { pcout << "  [ADE] ade_maxiTer=0, done.\n"; return 0; }

    // ════════════════════════════════════════════════════════════════════════════
    // PHASE 3: REACTIVE TRANSPORT SETUP
    // ════════════════════════════════════════════════════════════════════════════
    pcout << "\n┌────────────────────────────────────────────────────────────────────────┐\n";
    pcout << "│ PHASE 3: REACTIVE TRANSPORT SETUP                                     │\n";
    pcout << "└────────────────────────────────────────────────────────────────────────┘\n";

    T refNu, refTau;
    if (Pe > thrd) {
        refNu = PoreMeanU * charcs_length / Pe;
        refTau = refNu * RXNDES<T>::invCs2 + 0.5;
        if (refTau > 2 || refTau <= 0.5) { pcout << "  [ADE] ERROR: tau=" << refTau << " invalid\n"; return -1; }
    }
    else { refTau = tau; refNu = RXNDES<T>::cs2 * (refTau - 0.5); }
    T refOmega = 1/refTau;
    T ade_dt = refNu * dx * dx / vec_solute_poreD[0];

    std::vector<T> substrNUinPore(num_of_substrates), substrTAUinPore(num_of_substrates), substrOMEGAinPore(num_of_substrates), substrOMEGAinbFilm(num_of_substrates);
    for (plint iS = 0; iS < num_of_substrates; ++iS) {
        if (iS == 0) { substrNUinPore[iS]=refNu; substrTAUinPore[iS]=refTau; substrOMEGAinPore[iS]=refOmega; }
        else {
            substrNUinPore[iS] = substrNUinPore[0]*vec_solute_poreD[iS]/vec_solute_poreD[0];
            substrTAUinPore[iS] = substrNUinPore[iS]*RXNDES<T>::invCs2+0.5;
            substrOMEGAinPore[iS] = 1/substrTAUinPore[iS];
        }
        substrOMEGAinbFilm[iS] = 1/(refNu*vec_solute_bFilmD[iS]/vec_solute_poreD[0]*RXNDES<T>::invCs2+0.5);
    }

    std::vector<T> bioNUinPore(num_of_microbes), bioTAUinPore(num_of_microbes), bioOMEGAinPore(num_of_microbes), bioOMEGAinbFilm(num_of_microbes), bioTAUinbFilm(num_of_microbes);
    for (plint iM = 0; iM < num_of_microbes; ++iM) {
        if (vec_bMass_poreD[iM] > 0) {
            bioNUinPore[iM] = refNu * vec_bMass_poreD[iM] / vec_solute_poreD[0];
            bioTAUinPore[iM] = bioNUinPore[iM] * RXNDES<T>::invCs2 + 0.5;
            bioOMEGAinPore[iM] = 1/bioTAUinPore[iM];
        }
        else { bioNUinPore[iM] = 0.; bioTAUinPore[iM] = 0.; bioOMEGAinPore[iM] = 0.; }
        if (vec_bMass_bFilmD[iM] > 0) {
            bioOMEGAinbFilm[iM] = 1/(refNu*vec_bMass_bFilmD[iM]/vec_bMass_poreD[iM]*RXNDES<T>::invCs2+0.5);
            bioTAUinbFilm[iM] = 1/bioOMEGAinbFilm[iM];
        }
        else { bioOMEGAinbFilm[iM] = 0.; bioTAUinbFilm[iM] = 0.; }
    }

    pcout << "  [ADE] dt=" << ade_dt << " s/iter, total=" << ade_maxiTer*ade_dt << " s\n";

    // Create substrate lattices
    pcout << "  [ADE] Creating " << num_of_substrates << " substrate lattices...\n";
    MultiBlockLattice3D<T,RXNDES> substrLattice(nx, ny, nz, new AdvectionDiffusionBGKdynamics<T,RXNDES>(refOmega));
    std::vector< MultiBlockLattice3D<T,RXNDES> > vec_substr_lattices(num_of_substrates, substrLattice);
    std::vector< MultiBlockLattice3D<T,RXNDES> > dC(num_of_substrates, substrLattice);
    std::vector< MultiBlockLattice3D<T,RXNDES> > dC0(num_of_substrates, substrLattice);
    for (plint iS = 0; iS < num_of_substrates; ++iS) {
        soluteDomainSetup(vec_substr_lattices[iS], createLocalAdvectionDiffusionBoundaryCondition3D<T,RXNDES>(), geometry,
                          substrOMEGAinbFilm[iS], substrOMEGAinPore[iS], pore_dynamics, bounce_back, no_dynamics, bio_dynamics,
                          vec_c0[iS], vec_left_btype[iS], vec_right_btype[iS], vec_left_bcondition[iS], vec_right_bcondition[iS]);
        soluteDomainSetup(dC[iS], createLocalAdvectionDiffusionBoundaryCondition3D<T,RXNDES>(), geometry,
                          substrOMEGAinbFilm[iS], substrOMEGAinPore[iS], pore_dynamics, bounce_back, no_dynamics, bio_dynamics,
                          0., vec_left_btype[iS], vec_right_btype[iS], vec_left_bcondition[iS], vec_right_bcondition[iS]);
    }
    dC0=dC;

    // Create biomass lattices
    pcout << "  [ADE] Creating " << bfilm_count << " biofilm + " << bfree_count << " planktonic lattices...\n";
    MultiBlockLattice3D<T,RXNDES> initbFilmLattice(nx, ny, nz, new AdvectionDiffusionBGKdynamics<T,RXNDES>(0.));
    MultiBlockLattice3D<T,RXNDES> copybFilmLattice(nx, ny, nz, new AdvectionDiffusionBGKdynamics<T,RXNDES>(0.));
    MultiBlockLattice3D<T,RXNDES> initbFreeLattice(nx, ny, nz, new AdvectionDiffusionBGKdynamics<T,RXNDES>(0.));
    MultiBlockLattice3D<T,RXNDES> copybFreeLattice(nx, ny, nz, new AdvectionDiffusionBGKdynamics<T,RXNDES>(0.));
    std::vector< MultiBlockLattice3D<T,RXNDES> > vec_bFilm_lattices(bfilm_count, initbFilmLattice);
    std::vector< MultiBlockLattice3D<T,RXNDES> > vec_bFcopy_lattices(bfilm_count, copybFilmLattice);
    std::vector< MultiBlockLattice3D<T,RXNDES> > vec_bFree_lattices(bfree_count, initbFreeLattice);
    std::vector< MultiBlockLattice3D<T,RXNDES> > vec_bPcopy_lattices(bfree_count, copybFreeLattice);
    std::vector< MultiBlockLattice3D<T,RXNDES> > dBf(bfilm_count, initbFilmLattice);
    std::vector< MultiBlockLattice3D<T,RXNDES> > dBp(bfree_count, initbFreeLattice);
    std::vector< MultiBlockLattice3D<T,RXNDES> > dBf0(bfilm_count, initbFilmLattice);
    std::vector< MultiBlockLattice3D<T,RXNDES> > dBp0(bfree_count, initbFreeLattice);

    plint tmpIT0=0, tmpIT1=0;
    std::vector<plint> loctrack;
    for (plint iM = 0; iM < num_of_microbes; ++iM) {
        if (bmass_type[iM]==1) {
            bmassDomainSetup(vec_bFilm_lattices[tmpIT0], createLocalAdvectionDiffusionBoundaryCondition3D<T,RXNDES>(), geometry, bioOMEGAinPore[iM], bioOMEGAinbFilm[iM],
                             pore_dynamics, bounce_back, no_dynamics, bio_dynamics, bio_left_btype[iM], bio_right_btype[iM], bio_left_bcondition[iM], bio_right_bcondition[iM]);
            bmassDomainSetup(vec_bFcopy_lattices[tmpIT0], createLocalAdvectionDiffusionBoundaryCondition3D<T,RXNDES>(), geometry, 0., 0.,
                             pore_dynamics, bounce_back, no_dynamics, bio_dynamics, bio_left_btype[iM], bio_right_btype[iM], bio_left_bcondition[iM], bio_right_bcondition[iM]);
            bmassDomainSetup(dBf[tmpIT0], createLocalAdvectionDiffusionBoundaryCondition3D<T,RXNDES>(), geometry, 0., 0.,
                             pore_dynamics, bounce_back, no_dynamics, bio_dynamics, bio_left_btype[iM], bio_right_btype[iM], bio_left_bcondition[iM], bio_right_bcondition[iM]);
            loctrack.push_back(tmpIT0); ++tmpIT0;
        }
        else {
            if (solver_type[iM]==3) {
                soluteDomainSetup(vec_bFree_lattices[tmpIT1], createLocalAdvectionDiffusionBoundaryCondition3D<T,RXNDES>(), geometry, bioOMEGAinbFilm[iM], bioOMEGAinPore[iM],
                                  pore_dynamics, bounce_back, no_dynamics, bio_dynamics, vec_b0_free[tmpIT1], bio_left_btype[iM], bio_right_btype[iM], bio_left_bcondition[iM], bio_right_bcondition[iM]);
                bmassDomainSetup(vec_bPcopy_lattices[tmpIT1], createLocalAdvectionDiffusionBoundaryCondition3D<T,RXNDES>(), geometry, 0., 0.,
                                 pore_dynamics, bounce_back, no_dynamics, bio_dynamics, bio_left_btype[iM], bio_right_btype[iM], bio_left_bcondition[iM], bio_right_bcondition[iM]);
                bmassDomainSetup(dBp[tmpIT1], createLocalAdvectionDiffusionBoundaryCondition3D<T,RXNDES>(), geometry, 0., 0.,
                                 pore_dynamics, bounce_back, no_dynamics, bio_dynamics, bio_left_btype[iM], bio_right_btype[iM], bio_left_bcondition[iM], bio_right_bcondition[iM]);
            }
            else if (solver_type[iM]==1) { pcout << "  [ADE] ERROR: FD not implemented\n"; return -1; }
            loctrack.push_back(tmpIT1); ++tmpIT1;
        }
    }
    dBp0=dBp; dBf0=dBf;
    
    MultiBlockLattice3D<T,RXNDES> totalbFilmLattice(nx, ny, nz, new AdvectionDiffusionBGKdynamics<T,RXNDES>(0.));
    bmassDomainSetup(totalbFilmLattice, createLocalAdvectionDiffusionBoundaryCondition3D<T,RXNDES>(), geometry, bioOMEGAinPore[0], bioOMEGAinbFilm[0],
                     pore_dynamics, bounce_back, no_dynamics, bio_dynamics, bio_left_btype[0], bio_right_btype[0], bio_left_bcondition[0], bio_right_bcondition[0]);
    bmassDomainSetup(copybFilmLattice, createLocalAdvectionDiffusionBoundaryCondition3D<T,RXNDES>(), geometry, 0., 0.,
                     pore_dynamics, bounce_back, no_dynamics, bio_dynamics, bio_left_btype[0], bio_right_btype[0], bio_left_bcondition[0], bio_right_bcondition[0]);

    // Initialize biomass
    for (plint iM = 0; iM < bfilm_count; ++iM) {
        applyProcessingFunctional(new initializeScalarLattice3D<T,RXNDES,int>(vec_b0_film[iM], bio_dynamics[iM]), vec_bFilm_lattices[iM].getBoundingBox(), vec_bFilm_lattices[iM], geometry);
        std::vector<T> vec_b1(vec_b0_film[iM].size(),0.);
        applyProcessingFunctional(new initializeScalarLattice3D<T,RXNDES,int>(vec_b1, bio_dynamics[iM]), vec_bFcopy_lattices[iM].getBoundingBox(), vec_bFcopy_lattices[iM], geometry);
        initTotalbFilmLatticeDensity(vec_bFilm_lattices[iM], totalbFilmLattice);
    }

    if (bfilm_count > 0) {
        diag_initial_biomass = computeMax(*computeDensity(totalbFilmLattice));
        pcout << "  [ADE] Initial max biomass: " << diag_initial_biomass << " kg/m3\n";
    }

    // Mask and distance lattices
    MultiBlockLattice3D<T,RXNDES> maskLattice(nx, ny, nz, new AdvectionDiffusionBGKdynamics<T,RXNDES>(0.));
    MultiBlockLattice3D<T,RXNDES> ageLattice(nx, ny, nz, new AdvectionDiffusionBGKdynamics<T,RXNDES>(0.));
    MultiBlockLattice3D<T,RXNDES> distLattice(nx, ny, nz, new AdvectionDiffusionBGKdynamics<T,RXNDES>(0.));
    defineMaskLatticeDynamics(totalbFilmLattice, maskLattice, thrd_bFilmFrac);
    applyProcessingFunctional(new CopyGeometryScalar2maskLattice3D<T,RXNDES,int>(bio_dynamics), maskLattice.getBoundingBox(), maskLattice, geometry);
    applyProcessingFunctional(new CopyGeometryScalar2ageLattice3D<T,RXNDES,int>(), ageLattice.getBoundingBox(), ageLattice, ageDomain);
    applyProcessingFunctional(new CopyGeometryScalar2distLattice3D<T,RXNDES,int>(), distLattice.getBoundingBox(), distLattice, distanceDomain);
    pcout << "  [ADE] All lattices created\n";

    // Pointer vectors
    std::vector< MultiBlockLattice3D<T, RXNDES>* > substrate_lattices;
    for (plint iS = 0; iS < num_of_substrates; ++iS) { substrate_lattices.push_back(&vec_substr_lattices[iS]); }
    substrate_lattices.push_back(&maskLattice);

    std::vector< MultiBlockLattice3D<T, RXNDES>* > planktonic_lattices;
    for (size_t iP = 0; iP < vec_bFree_lattices.size(); ++iP) { planktonic_lattices.push_back(&vec_bFree_lattices[iP]); }
    planktonic_lattices.push_back(&maskLattice);

    std::vector< MultiBlockLattice3D<T, RXNDES>* > ptr_kns_lattices;
    for (plint iS = 0; iS < num_of_substrates; ++iS) { ptr_kns_lattices.push_back(&vec_substr_lattices[iS]); }
    for (plint iM = 0; iM < num_of_microbes; ++iM) {
        if (bmass_type[iM]==1) { if (reaction_type[iM]==1) ptr_kns_lattices.push_back(&vec_bFilm_lattices[loctrack[iM]]); }
        else { if (reaction_type[iM]==1) ptr_kns_lattices.push_back(&vec_bFree_lattices[loctrack[iM]]); }
    }
    for (plint iS = 0; iS < num_of_substrates; ++iS) { ptr_kns_lattices.push_back(&dC[iS]); }
    for (plint iM = 0; iM < num_of_microbes; ++iM) {
        if (bmass_type[iM]==1) { if (reaction_type[iM]==1) ptr_kns_lattices.push_back(&dBf[loctrack[iM]]); }
        else { if (reaction_type[iM]==1) ptr_kns_lattices.push_back(&dBp[loctrack[iM]]); }
    }
    ptr_kns_lattices.push_back(&maskLattice);

    std::vector< MultiBlockLattice3D<T, RXNDES>* > ptr_update_rxnLattices;
    for (plint iS = 0; iS < num_of_substrates; ++iS) { ptr_update_rxnLattices.push_back(&vec_substr_lattices[iS]); }
    for (plint iM = 0; iM < num_of_microbes; ++iM) {
        if (bmass_type[iM]==1) ptr_update_rxnLattices.push_back(&vec_bFilm_lattices[loctrack[iM]]);
        else ptr_update_rxnLattices.push_back(&vec_bFree_lattices[loctrack[iM]]);
    }
    for (plint iS = 0; iS < num_of_substrates; ++iS) { ptr_update_rxnLattices.push_back(&dC[iS]); }
    for (plint iM = 0; iM < num_of_microbes; ++iM) {
        if (bmass_type[iM]==1) ptr_update_rxnLattices.push_back(&dBf[loctrack[iM]]);
        else ptr_update_rxnLattices.push_back(&dBp[loctrack[iM]]);
    }
    ptr_update_rxnLattices.push_back(&maskLattice);

    std::vector< MultiBlockLattice3D<T, RXNDES>* > ptr_ca_lattices;
    for (plint iM = 0; iM < num_of_microbes; ++iM) {
        if (solver_type[iM]==2) {
            if (bmass_type[iM]==1) ptr_ca_lattices.push_back(&vec_bFilm_lattices[loctrack[iM]]);
            else { pcout << "  [CA] ERROR: CA only for biofilm\n"; return -1; }
        }
    }
    for (plint iM = 0; iM < num_of_microbes; ++iM) { if (solver_type[iM]==2) ptr_ca_lattices.push_back(&vec_bFcopy_lattices[loctrack[iM]]); }
    ptr_ca_lattices.push_back(&totalbFilmLattice);
    ptr_ca_lattices.push_back(&maskLattice);
    ptr_ca_lattices.push_back(&ageLattice);
    plint caLlen = ptr_ca_lattices.size();

    std::vector< MultiBlockLattice3D<T, RXNDES>* > ptr_fd_lattices;
    for (plint iM = 0; iM < num_of_microbes; ++iM) {
        if (solver_type[iM]==1) {
            if (bmass_type[iM]==1) ptr_fd_lattices.push_back(&vec_bFilm_lattices[loctrack[iM]]);
            else ptr_fd_lattices.push_back(&vec_bFree_lattices[loctrack[iM]]);
        }
    }
    for (plint iM = 0; iM < num_of_microbes; ++iM) {
        if (solver_type[iM]==1) {
            if (bmass_type[iM]==1) ptr_fd_lattices.push_back(&vec_bFcopy_lattices[loctrack[iM]]);
            else ptr_fd_lattices.push_back(&vec_bPcopy_lattices[loctrack[iM]]);
        }
    }
    ptr_fd_lattices.push_back(&maskLattice);
    plint fdLlen = ptr_fd_lattices.size();

    std::vector< MultiBlockLattice3D<T, RXNDES>* > ptr_eq_lattices;
    for (plint iS = 0; iS < num_of_substrates; ++iS) { ptr_eq_lattices.push_back(&vec_substr_lattices[iS]); }
    ptr_eq_lattices.push_back(&maskLattice);

    std::vector< MultiBlockLattice3D<T, RXNDES>* > ageNdistance_lattices;
    ageNdistance_lattices.push_back(&ageLattice);
    ageNdistance_lattices.push_back(&distLattice);
    ageNdistance_lattices.push_back(&totalbFilmLattice);

    // Initial mask update
    if (track_performance == 1) { global::timer("NS").restart(); }
    plint old_totMask = util::roundToInt(computeAverage(*computeDensity(maskLattice))*nx*ny*nz);
    if (bfilm_count > 0) {
        applyProcessingFunctional(new updateLocalMaskNtotalLattices3D<T,RXNDES>(nx, ny, nz, caLlen, bounce_back, no_dynamics, bio_dynamics, pore_dynamics, thrd_bFilmFrac, max_bMassRho), vec_bFilm_lattices[0].getBoundingBox(), ptr_ca_lattices);
    }
    plint new_totMask = util::roundToInt(computeAverage(*computeDensity(maskLattice))*nx*ny*nz);
    if (std::abs(old_totMask-new_totMask)>0) {
        old_totMask = new_totMask;
        if (soluteDindex == 1) applyProcessingFunctional(new updateSoluteDynamics3D<T,RXNDES>(num_of_substrates, bounce_back, no_dynamics, pore_dynamics, substrOMEGAinbFilm, substrOMEGAinPore), vec_substr_lattices[0].getBoundingBox(), substrate_lattices);
        if (bmassDindex == 1) applyProcessingFunctional(new updateBiomassDynamics3D<T,RXNDES>((plint)vec_bFree_lattices.size(), bounce_back, no_dynamics, pore_dynamics, bioOMEGAinbFilm, bioOMEGAinPore), vec_bFree_lattices[0].getBoundingBox(), planktonic_lattices);
        applyProcessingFunctional(new updateNsLatticesDynamics3D<T,NSDES,T,RXNDES>(nsLatticeOmega, vec_permRatio[0], pore_dynamics, no_dynamics, bounce_back), nsLattice.getBoundingBox(), nsLattice, maskLattice);
        for (plint iT2 = 0; iT2 < ns_maxiTer_1; ++iT2) {
            nsLattice.collideAndStream();
            ns_convg1.takeValue(getStoredAverageEnergy(nsLattice),false);
            if (ns_convg1.hasConverged()) break;
        }
    }
    if (read_NS_file==0 || (read_NS_file==1 && ns_rerun_iT0>0)) {
        if (track_performance == 0) {
            writeNsVTI(nsLattice,ns_maxiTer_1,"nsLatticeFinal1_");
            saveBinaryBlock(nsLattice, str_outputDir+ns_filename+".chk");
        }
    }
    if (track_performance == 1) { nstime += global::timer("NS").getTime(); global::timer("NS").stop(); }

    // Couple NS and ADE
    if (Pe > thrd) {
        pcout << "  [ADE] Coupling NS-ADE lattices...\n";
        for (plint iS = 0; iS < num_of_substrates; ++iS) {
            latticeToPassiveAdvDiff(nsLattice, vec_substr_lattices[iS], vec_substr_lattices[iS].getBoundingBox());
        }
        tmpIT0=0;
        for (plint iM = 0; iM < num_of_substrates; ++iM) {
            if (solver_type[iM] == 3) {
                latticeToPassiveAdvDiff(nsLattice, vec_bFree_lattices[tmpIT0], vec_bFree_lattices[tmpIT0].getBoundingBox());
                ++tmpIT0;
            }
        }
        pcout << "  [ADE] Stabilizing (10000 iter)...\n";
        for (plint iT=0; iT<10000; ++iT) {
            for (plint iS = 0; iS < num_of_substrates; ++iS) vec_substr_lattices[iS].collideAndStream();
            for (size_t iM = 0; iM < vec_bFree_lattices.size(); ++iM) vec_bFree_lattices[iM].collideAndStream();
        }
        for (plint iS = 0; iS < num_of_substrates; ++iS) applyProcessingFunctional(new stabilizeADElattice3D<T,RXNDES,int>(vec_c0[iS], pore_dynamics, bio_dynamics), vec_substr_lattices[iS].getBoundingBox(), vec_substr_lattices[iS], geometry);
        for (size_t iM = 0; iM < vec_bFree_lattices.size(); ++iM) applyProcessingFunctional(new stabilizeADElattice3D<T,RXNDES,int>(vec_b0_free[iM], pore_dynamics, bio_dynamics), vec_bFree_lattices[iM].getBoundingBox(), vec_bFree_lattices[iM], geometry);
    }

    // Load checkpoints if needed
    iT = 0;
    if (read_ADE_file==1 && ade_rerun_iT0>0) {
        pcout << "  [ADE] Loading checkpoints...\n";
        for (plint iS = 0; iS < num_of_substrates; ++iS) loadBinaryBlock(vec_substr_lattices[iS], str_outputDir+ade_filename+"_"+std::to_string(iS));
        tmpIT0=0; tmpIT1=0;
        for (plint iM = 0; iM < num_of_microbes; ++iM) {
            if (bmass_type[iM]==1) { loadBinaryBlock(vec_bFilm_lattices[tmpIT0], str_outputDir+bio_filename+"_"+std::to_string(iM)); ++tmpIT0; }
            else { loadBinaryBlock(vec_bFree_lattices[tmpIT1], str_outputDir+bio_filename+"_"+std::to_string(iM)); ++tmpIT1; }
        }
        iT = ade_rerun_iT0;
    }
    T catime = 0, adetime = 0, knstime = 0, cnstime = 0;

    // ════════════════════════════════════════════════════════════════════════════
    // PHASE 4: MAIN SIMULATION LOOP
    // ════════════════════════════════════════════════════════════════════════════
    pcout << "\n┌────────────────────────────────────────────────────────────────────────┐\n";
    pcout << "│ PHASE 4: MAIN SIMULATION LOOP                                         │\n";
    pcout << "├────────────────────────────────────────────────────────────────────────┤\n";
    pcout << "│ Max iterations: " << ade_maxiTer << "   VTI interval: " << ade_VTI_iTer << "\n";
    pcout << "│ Output files will use SPECIES NAMES from XML:\n";
    for (plint iS = 0; iS < num_of_substrates; ++iS) pcout << "│   " << vec_subs_names[iS] << "_*.vti\n";
    for (plint iM = 0; iM < num_of_microbes; ++iM) pcout << "│   " << vec_microbes_names[iM] << "_*.vti\n";
    pcout << "└────────────────────────────────────────────────────────────────────────┘\n\n";

    global::timer("ade").restart();
    util::ValueTracer<T> ns_convg2(1.0,1000.0,ns_converge_iT2);
    bool ns_saturate=0, percolationFlag=0;

    for (; iT < ade_maxiTer; ++iT) {
        // ════════════════════════════════════════════════════════════════════════
        // VTI OUTPUT AND DIAGNOSTICS
        // ════════════════════════════════════════════════════════════════════════
        if (ade_VTI_iTer > 0 && iT % ade_VTI_iTer == 0) {
            pcout << "\n╔════════════════════════════════════════════════════════════════════════╗\n";
            pcout << "║ ITERATION " << iT << "  |  Time: " << std::scientific << iT*ade_dt << " s" << std::fixed << "\n";
            pcout << "╠════════════════════════════════════════════════════════════════════════╣\n";
            
            // Substrate status
            pcout << "║ SUBSTRATES:\n";
            for (plint iS = 0; iS < num_of_substrates; ++iS) {
                T sMin = computeMin(*computeDensity(vec_substr_lattices[iS]));
                T sMax = computeMax(*computeDensity(vec_substr_lattices[iS]));
                T sAvg = computeAverage(*computeDensity(vec_substr_lattices[iS]));
                pcout << "║   " << vec_subs_names[iS] << ": min=" << std::scientific << sMin 
                      << " avg=" << sAvg << " max=" << sMax;
                if (sMin < 0) pcout << " [NEG!]";
                pcout << std::fixed << "\n";
            }
            
            // Biomass status
            if (bfilm_count > 0) {
                pcout << "║ BIOMASS:\n";
                for (plint iM = 0; iM < bfilm_count; ++iM) {
                    T bMin = computeMin(*computeDensity(vec_bFilm_lattices[iM]));
                    T bMax = computeMax(*computeDensity(vec_bFilm_lattices[iM]));
                    T bAvg = computeAverage(*computeDensity(vec_bFilm_lattices[iM]));
                    T growth = (diag_initial_biomass > 0) ? ((bMax - diag_initial_biomass) / diag_initial_biomass * 100.0) : 0.0;
                    pcout << "║   " << vec_microbes_names[iM] << ": max=" << std::scientific << bMax 
                          << "/" << max_bMassRho << std::fixed << " (" << growth << "% growth)";
                    if (bMax > max_bMassRho) pcout << " [>Bmax!]";
                    pcout << "\n";
                }
                pcout << "║   CA: triggers=" << diag_ca_triggers << " redistributions=" << diag_ca_redistributions << "\n";
            }
            
            // ════════════════════════════════════════════════════════════════════
            // KINETICS DEBUG STATS (efficient - only summary)
            // ════════════════════════════════════════════════════════════════════
            if (kns_count > 0) {
                long cells_bio, cells_grow;
                double sum_dB, max_B, max_dB, min_DOC;
                KineticsStats::getStats(cells_bio, cells_grow, sum_dB, max_B, max_dB, min_DOC);
                pcout << "║ KINETICS (last " << ade_VTI_iTer << " iters):\n";
                pcout << "║   Active cells: " << cells_bio << " (growing: " << cells_grow << ")\n";
                if (cells_bio > 0) {
                    pcout << "║   Sum dB/dt: " << std::scientific << sum_dB << " kg/m³/s\n";
                    pcout << "║   Max dB/dt: " << max_dB << " kg/m³/s\n";
                    pcout << "║   Min DOC in biofilm: " << min_DOC << " mol/L\n";
                    // Estimate iterations to Bmax
                    if (max_dB > 0 && max_B < max_bMassRho) {
                        double time_to_bmax = (max_bMassRho - max_B) / max_dB;
                        double iters_to_bmax = time_to_bmax / ade_dt;
                        pcout << "║   Est. iters to Bmax: " << std::fixed << (long)iters_to_bmax << "\n";
                    }
                    pcout << std::fixed;
                }
                // Reset stats for next interval
                KineticsStats::resetIteration();
            }
            
            pcout << "╚════════════════════════════════════════════════════════════════════════╝\n";
            
            // Write VTI with SPECIES NAMES
            if (track_performance == 0) {
                for (plint iS = 0; iS < num_of_substrates; ++iS) {
                    writeAdvVTI(vec_substr_lattices[iS], iT, vec_subs_names[iS]+"_");
                }
                tmpIT0=0; tmpIT1=0;
                for (plint iM = 0; iM < num_of_microbes; ++iM) {
                    if (bmass_type[iM]==1) { writeAdvVTI(vec_bFilm_lattices[tmpIT0], iT, vec_microbes_names[iM]+"_"); ++tmpIT0; }
                    else { writeAdvVTI(vec_bFree_lattices[tmpIT1], iT, vec_microbes_names[iM]+"_"); ++tmpIT1; }
                }
                if (Pe > thrd) writeNsVTI(nsLattice, iT, "nsLattice_");
            }
            adetime += global::timer("ade").getTime();
            pcout << "  Wall clock: " << global::timer("ade").getTime() << " s\n";
            global::timer("ade").restart();
        }
        
        // Checkpoint
        if (ade_CHK_iTer > 0 && iT % ade_CHK_iTer == 0 && iT > 0 && track_performance == 0) {
            pcout << "  [CHK] Saving checkpoint at iter=" << iT << "\n";
            for (plint iS = 0; iS < num_of_substrates; ++iS)
                saveBinaryBlock(vec_substr_lattices[iS], str_outputDir + ade_filename + std::to_string(iS) + "_" + std::to_string(iT) + ".chk");
            tmpIT0=0; tmpIT1=0;
            for (plint iM = 0; iM < num_of_microbes; ++iM) {
                if (bmass_type[iM]==1) { saveBinaryBlock(vec_bFilm_lattices[tmpIT0], str_outputDir + bio_filename + std::to_string(iM) + "_" + std::to_string(iT) + ".chk"); ++tmpIT0; }
                else { saveBinaryBlock(vec_bFree_lattices[tmpIT1], str_outputDir + bio_filename + std::to_string(iM) + "_" + std::to_string(iT) + ".chk"); ++tmpIT1; }
            }
        }

        if (track_performance == 1) global::timer("cns").restart();
        
        // Collision
        for (plint iS = 0; iS < num_of_substrates; ++iS) vec_substr_lattices[iS].collide();
        if (lb_count > 0) {
            for (plint iM = 0; iM < num_of_microbes; ++iM) {
                if (solver_type[iM]==3) {
                    if (bmass_type[iM]==1) vec_bFilm_lattices[loctrack[iM]].collide();
                    else vec_bFree_lattices[loctrack[iM]].collide();
                }
            }
        }
        if (track_performance == 1) { cnstime += global::timer("cns").getTime(); global::timer("cns").stop(); }

        // Kinetics (only if enable_kinetics is true)
        dC=dC0; dBp=dBp0; dBf=dBf0;
        if (enable_kinetics && kns_count > 0) {
            if (track_performance == 1) global::timer("kns").restart();
            applyProcessingFunctional(new run_kinetics<T,RXNDES>(nx, num_of_substrates, kns_count, ade_dt, vec_Kc_kns, vec_mu_kns, no_dynamics, bounce_back),
                                      vec_substr_lattices[0].getBoundingBox(), ptr_kns_lattices);
            if (track_performance == 1) { knstime+=global::timer("kns").getTime(); global::timer("kns").stop(); }
        }
        if (enable_kinetics && rxn_count > 0) {
            if (track_performance == 1) global::timer("rxn").restart();
            applyProcessingFunctional(new update_rxnLattices<T,RXNDES>(nx, num_of_substrates, num_of_microbes, no_dynamics, bounce_back),
                                      vec_substr_lattices[0].getBoundingBox(), ptr_update_rxnLattices);
            if (track_performance == 1) { T rxntime=global::timer("rxn").getTime(); global::timer("rxn").stop(); if (kns_count>0) knstime+=rxntime; }
        }

        // Equilibrium chemistry (runs regardless of enable_kinetics - controlled separately)
        if (useEquilibrium) {
            if (track_performance == 1) global::timer("eq").restart();
            applyProcessingFunctional(new run_equilibrium_biotic<T, RXNDES>(nx, num_of_substrates, eqSolver, no_dynamics, bounce_back),
                                      vec_substr_lattices[0].getBoundingBox(), ptr_eq_lattices);
            if (track_performance == 1) { eqtime += global::timer("eq").getTime(); global::timer("eq").stop(); }
        }

        // ════════════════════════════════════════════════════════════════════════════
        // VALIDATION DIAGNOSTICS (per-iteration detailed output)
        // ════════════════════════════════════════════════════════════════════════════
        if (enable_validation_diagnostics && (iT % 100 == 0 || iT < 10)) {
            pcout << "\n┌─────────────────────────────────────────────────────────────────────────┐\n";
            pcout << "│ VALIDATION DIAGNOSTICS - Iteration " << iT << "                              │\n";
            pcout << "├─────────────────────────────────────────────────────────────────────────┤\n";
            pcout << "│ Time: " << std::scientific << std::setprecision(4) << iT*ade_dt << " s" << std::fixed << "\n";

            // Step-by-step data flow verification
            pcout << "├─────────────────────────────────────────────────────────────────────────┤\n";
            pcout << "│ STEP 6.1 [COLLISION]: LBM collision completed                           │\n";

            // Sample concentration at center of domain
            plint midX = nx/2, midY = ny/2, midZ = nz/2;
            pcout << "│ STEP 6.2 [KINETICS]: ";
            if (enable_kinetics && kns_count > 0) {
                pcout << "ACTIVE - " << kns_count << " reaction(s)\n";
                // Show sample values
                for (plint iS = 0; iS < std::min((plint)2, num_of_substrates); ++iS) {
                    T cMid = vec_substr_lattices[iS].get(midX, midY, midZ).computeDensity();
                    T dC_mid = dC[iS].get(midX, midY, midZ).computeDensity();
                    pcout << "│   " << vec_subs_names[iS] << " @center: C=" << std::scientific
                          << cMid << ", dC=" << dC_mid << std::fixed << "\n";
                }
                if (bfilm_count > 0) {
                    T bMid = vec_bFilm_lattices[0].get(midX, midY, midZ).computeDensity();
                    T dB_mid = dBf[0].get(midX, midY, midZ).computeDensity();
                    pcout << "│   Biomass @center: B=" << std::scientific << bMid
                          << ", dB=" << dB_mid << std::fixed << "\n";
                }
            } else {
                pcout << "DISABLED (enable_kinetics=" << enable_kinetics << ", kns_count=" << kns_count << ")\n";
            }

            pcout << "│ STEP 6.3 [EQUILIBRIUM]: ";
            if (useEquilibrium) {
                pcout << "ACTIVE\n";
                // Show sample equilibrium-adjusted values
                for (plint iS = 0; iS < std::min((plint)2, num_of_substrates); ++iS) {
                    T cMin = computeMin(*computeDensity(vec_substr_lattices[iS]));
                    T cMax = computeMax(*computeDensity(vec_substr_lattices[iS]));
                    pcout << "│   " << vec_subs_names[iS] << ": min=" << std::scientific
                          << cMin << ", max=" << cMax << std::fixed << "\n";
                }
            } else {
                pcout << "DISABLED\n";
            }

            // Mass balance check
            pcout << "├─────────────────────────────────────────────────────────────────────────┤\n";
            pcout << "│ MASS BALANCE CHECK:                                                     │\n";
            for (plint iS = 0; iS < std::min((plint)2, num_of_substrates); ++iS) {
                T totalMass = computeSum(*computeDensity(vec_substr_lattices[iS]));
                pcout << "│   " << vec_subs_names[iS] << " total: " << std::scientific << totalMass << std::fixed << "\n";
            }
            if (bfilm_count > 0) {
                T totalBiomass = computeSum(*computeDensity(totalbFilmLattice));
                pcout << "│   Total biomass: " << std::scientific << totalBiomass << std::fixed << "\n";
            }

            pcout << "└─────────────────────────────────────────────────────────────────────────┘\n";
        }

        // CA biomass expansion
        if (ca_count > 0) {
            applyProcessingFunctional(new updateLocalMaskNtotalLattices3D<T,RXNDES>(nx, ny, nz, caLlen, bounce_back, no_dynamics, bio_dynamics, pore_dynamics, thrd_bFilmFrac, max_bMassRho), vec_bFilm_lattices[0].getBoundingBox(), ptr_ca_lattices);
            T globalBmax = computeMax(*computeDensity(totalbFilmLattice));
            if (std::isnan(globalBmax)) { pcout << "\n  [CA] ERROR: NaN at iter=" << iT << "\n"; return -1; }
            plint whilecount=0;
            if (globalBmax - max_bMassRho > thrd) {
                diag_ca_triggers++;
                if (track_performance == 1) global::timer("ca").restart();
                while (globalBmax - max_bMassRho > thrd) {
                    for (plint iM=0; iM<bfilm_count; ++iM) vec_bFcopy_lattices[iM]=copybFilmLattice;
                    if (halfflag == 0) applyProcessingFunctional(new pushExcessBiomass3D<T,RXNDES>(max_bMassRho, nx, ny, nz, 1, caLlen, no_dynamics, bounce_back, pore_dynamics), vec_bFilm_lattices[0].getBoundingBox(), ptr_ca_lattices);
                    else applyProcessingFunctional(new halfPushExcessBiomass3D<T,RXNDES>(max_bMassRho, nx, ny, nz, 1, caLlen, no_dynamics, bounce_back, pore_dynamics), vec_bFilm_lattices[0].getBoundingBox(), ptr_ca_lattices);
                    applyProcessingFunctional(new pullExcessBiomass3D<T,RXNDES>(nx, ny, nz, 1, caLlen), vec_bFilm_lattices[0].getBoundingBox(), ptr_ca_lattices);
                    applyProcessingFunctional(new updateLocalMaskNtotalLattices3D<T,RXNDES>(nx, ny, nz, caLlen, bounce_back, no_dynamics, bio_dynamics, pore_dynamics, thrd_bFilmFrac, max_bMassRho), vec_bFilm_lattices[0].getBoundingBox(), ptr_ca_lattices);
                    globalBmax = computeMax(*computeDensity(totalbFilmLattice));
                    diag_ca_redistributions++;
                    if (whilecount%50 == 0) {
                        plint diff = 1, whilecount1 = 0;
                        while (diff != 0) {
                            plint old_totAge = util::roundToInt(computeAverage(*computeDensity(ageLattice))*nx*ny*nz);
                            applyProcessingFunctional(new updateAgeDistance3D<T,RXNDES>(max_bMassRho, nx, ny, nz), ageLattice.getBoundingBox(), ageNdistance_lattices);
                            plint new_totAge = util::roundToInt(computeAverage(*computeDensity(ageLattice))*nx*ny*nz);
                            diff = new_totAge-old_totAge;
                            ++whilecount1;
                            if (whilecount1 > 1000) { pcout << "\n  [CA] ERROR: Stuck in age loop\n"; exit(EXIT_FAILURE); }
                        }
                    }
                    if (whilecount > 2000) { pcout << "\n  [CA] ERROR: Stuck in push-pull loop\n"; exit(EXIT_FAILURE); }
                    ++whilecount;
                }
                if (track_performance == 1) { catime+=global::timer("ca").getTime(); global::timer("ca").stop(); }
            }
        }
        if (fd_count > 0) {
            applyProcessingFunctional(new updateLocalMaskNtotalLattices3D<T,RXNDES>(nx, ny, nz, fdLlen, bounce_back, no_dynamics, bio_dynamics, pore_dynamics, thrd_bFilmFrac, max_bMassRho), vec_bFilm_lattices[0].getBoundingBox(), ptr_fd_lattices);
            for (plint iM=0; iM<bfilm_count; ++iM) vec_bFcopy_lattices[iM]=vec_bFilm_lattices[iM];
            for (plint iP=0; iP<bfree_count; ++iP) vec_bPcopy_lattices[iP]=vec_bFree_lattices[iP];
            applyProcessingFunctional(new fdDiffusion3D<T,RXNDES>(nx, ny, nz, fdLlen, 1, bioNUinPore[0]), vec_bFilm_lattices[0].getBoundingBox(), ptr_fd_lattices);
            applyProcessingFunctional(new updateLocalMaskNtotalLattices3D<T,RXNDES>(nx, ny, nz, fdLlen, bounce_back, no_dynamics, bio_dynamics, pore_dynamics, thrd_bFilmFrac, max_bMassRho), vec_bFilm_lattices[0].getBoundingBox(), ptr_fd_lattices);
        }

        // Update flow and dynamics
        if (ca_count > 0 || fd_count > 0) {
            if (track_performance == 1) global::timer("ca").restart();
            new_totMask = util::roundToInt(computeAverage(*computeDensity(maskLattice))*nx*ny*nz);
            if (std::abs(old_totMask-new_totMask)>0) {
                old_totMask = new_totMask;
                applyProcessingFunctional(new updateAgeDistance3D<T,RXNDES>(max_bMassRho, nx, ny, nz), ageLattice.getBoundingBox(), ageNdistance_lattices);
                if (iT % ade_update_interval == 0) {
                    if (soluteDindex == 1) applyProcessingFunctional(new updateSoluteDynamics3D<T,RXNDES>(num_of_substrates, bounce_back, no_dynamics, pore_dynamics, substrOMEGAinbFilm, substrOMEGAinPore), vec_substr_lattices[0].getBoundingBox(), substrate_lattices);
                    if (bmassDindex == 1) applyProcessingFunctional(new updateBiomassDynamics3D<T,RXNDES>((plint)vec_bFree_lattices.size(), bounce_back, no_dynamics, pore_dynamics, bioOMEGAinbFilm, bioOMEGAinPore), vec_bFree_lattices[0].getBoundingBox(), planktonic_lattices);
                }
                if (track_performance == 1) { catime+=global::timer("ca").getTime(); global::timer("ca").stop(); }
                if (iT % ns_update_interval == 0 && Pe > thrd && ns_saturate == 0) {
                    if (track_performance == 1) global::timer("NS").restart();
                    applyProcessingFunctional(new updateNsLatticesDynamics3D<T,NSDES,T,RXNDES>(nsLatticeOmega, vec_permRatio[0], pore_dynamics, no_dynamics, bounce_back), nsLattice.getBoundingBox(), nsLattice, maskLattice);
                    for (plint iT2 = 0; iT2 < ns_maxiTer_2; ++iT2) {
                        nsLattice.collideAndStream();
                        ns_convg2.takeValue(getStoredAverageEnergy(nsLattice),false);
                        if (ns_convg2.hasConverged()) break;
                        if (iT2 == (ns_maxiTer_2-1)) ns_saturate = 1;
                    }
                    if (ns_saturate == 1) {
                        T outletvel = computeAverage(*computeVelocityComponent(nsLattice, Box3D(nx-2,nx-2, 0,ny-1, 0,nz-1), 0));
                        if (outletvel > thrd) ns_saturate = 0;
                        else { pcout << "\n  [NS] Percolation limit reached at iter=" << iT << "\n"; percolationFlag = 1; }
                    }
                    for (plint iS = 0; iS < num_of_substrates; ++iS) latticeToPassiveAdvDiff(nsLattice, vec_substr_lattices[iS], vec_substr_lattices[iS].getBoundingBox());
                    if (lb_count > 0) {
                        for (plint iM = 0; iM < num_of_microbes; ++iM) {
                            if (solver_type[iM]==3) {
                                if (bmass_type[iM]==1) latticeToPassiveAdvDiff(nsLattice, vec_bFilm_lattices[loctrack[iM]], vec_bFilm_lattices[loctrack[iM]].getBoundingBox());
                                else latticeToPassiveAdvDiff(nsLattice, vec_bFree_lattices[loctrack[iM]], vec_bFree_lattices[loctrack[iM]].getBoundingBox());
                            }
                        }
                    }
                    if (track_performance == 1) { nstime += global::timer("NS").getTime(); global::timer("NS").stop(); }
                }
            }
            else { if (track_performance == 1) { catime+=global::timer("ca").getTime(); global::timer("ca").stop(); } }
        }

        // Streaming
        if (track_performance == 1) global::timer("cns").restart();
        for (plint iS = 0; iS < num_of_substrates; ++iS) vec_substr_lattices[iS].stream();
        if (lb_count > 0) {
            for (plint iM = 0; iM < num_of_microbes; ++iM) {
                if (solver_type[iM]==3) {
                    if (bmass_type[iM]==1) vec_bFilm_lattices[loctrack[iM]].stream();
                    else vec_bFree_lattices[loctrack[iM]].stream();
                }
            }
        }
        if (track_performance == 1) { nstime += global::timer("cns").getTime(); global::timer("cns").stop(); }
        if (percolationFlag == 1) break;
    }
    // ════════════════════════════════════════════════════════════════════════════
    // PHASE 7: FINAL OUTPUT FILES
    // ════════════════════════════════════════════════════════════════════════════
    pcout << "\n┌────────────────────────────────────────────────────────────────────────┐\n";
    pcout << "│ PHASE 7: WRITING FINAL OUTPUT FILES                                   │\n";
    pcout << "└────────────────────────────────────────────────────────────────────────┘\n";

    // Final output
    if (track_performance == 0) {
        pcout << "  Saving VTI and CHK files...\n";
        for (plint iS = 0; iS < num_of_substrates; ++iS) {
            writeAdvVTI(vec_substr_lattices[iS], iT, vec_subs_names[iS]+"_");
            saveBinaryBlock(vec_substr_lattices[iS], str_outputDir+ade_filename+std::to_string(iS)+"_"+std::to_string(iT)+".chk");
            pcout << "    [OK] " << vec_subs_names[iS] << " saved\n";
        }
        tmpIT0=0; tmpIT1=0;
        for (plint iM = 0; iM < num_of_microbes; ++iM) {
            if (bmass_type[iM]==1) {
                writeAdvVTI(vec_bFilm_lattices[tmpIT0], iT, vec_microbes_names[iM]+"_");
                saveBinaryBlock(vec_bFilm_lattices[tmpIT0], str_outputDir+bio_filename+std::to_string(iM)+"_"+std::to_string(iT)+".chk");
                pcout << "    [OK] " << vec_microbes_names[iM] << " saved\n";
                ++tmpIT0;
            }
            else {
                writeAdvVTI(vec_bFree_lattices[tmpIT1], iT, vec_microbes_names[iM]+"_");
                saveBinaryBlock(vec_bFree_lattices[tmpIT1], str_outputDir+bio_filename+std::to_string(iM)+"_"+std::to_string(iT)+".chk");
                pcout << "    [OK] " << vec_microbes_names[iM] << " saved\n";
                ++tmpIT1;
            }
        }
        writeAdvVTI(maskLattice, iT, mask_filename+"_");
        saveBinaryBlock(maskLattice, str_outputDir+mask_filename+"_"+std::to_string(iT)+".chk");
        pcout << "    [OK] Mask lattice saved\n";
        if (Pe > thrd) {
            writeNsVTI(nsLattice, iT, "nsLattice_");
            saveBinaryBlock(nsLattice, str_outputDir+ns_filename+".chk");
            pcout << "    [OK] Flow field saved\n";
        }
    }

    // ════════════════════════════════════════════════════════════════════════════
    // PHASE 8-9: SUMMARY AND STATISTICS
    // ════════════════════════════════════════════════════════════════════════════
    T TET = global::timer("total").getTime(); global::timer("total").stop();

    pcout << "\n╔══════════════════════════════════════════════════════════════════════════╗\n";
    pcout << "║                         SIMULATION COMPLETE                              ║\n";
    pcout << "╠══════════════════════════════════════════════════════════════════════════╣\n";
    pcout << "║ TIMING:                                                                  ║\n";
    pcout << "║   Total iterations: " << iT << "\n";
    pcout << "║   Simulated time:   " << std::scientific << iT*ade_dt << " s\n" << std::fixed;
    pcout << "║   Wall clock:       " << TET << " s (" << TET/60 << " min)\n";
    pcout << "╠══════════════════════════════════════════════════════════════════════════╣\n";
    pcout << "║ SIMULATION MODE:                                                         ║\n";
    pcout << "║   Biotic mode:      " << (biotic_mode ? "YES (with microbes)" : "NO (abiotic)") << "\n";
    pcout << "║   Kinetics:         " << (enable_kinetics ? "ENABLED" : "DISABLED") << "\n";
    pcout << "║   Equilibrium:      " << (useEquilibrium ? "ENABLED" : "DISABLED") << "\n";
    pcout << "║   Validation diag:  " << (enable_validation_diagnostics ? "ENABLED" : "DISABLED") << "\n";
    if (bfilm_count > 0) {
        T finalBmax = computeMax(*computeDensity(totalbFilmLattice));
        T totalGrowth = (diag_initial_biomass > 0) ? ((finalBmax - diag_initial_biomass) / diag_initial_biomass * 100.0) : 0.0;
        pcout << "╠══════════════════════════════════════════════════════════════════════════╣\n";
        pcout << "║ BIOMASS RESULTS:                                                         ║\n";
        pcout << "║   Initial max:      " << std::scientific << diag_initial_biomass << " kg/m³\n";
        pcout << "║   Final max:        " << finalBmax << " kg/m³\n" << std::fixed;
        pcout << "║   Growth:           " << totalGrowth << "%\n";
        pcout << "║   CA triggers:      " << diag_ca_triggers << "\n";
        pcout << "║   Redistributions:  " << diag_ca_redistributions << "\n";
    }
    pcout << "╠══════════════════════════════════════════════════════════════════════════╣\n";
    pcout << "║ FINAL CONCENTRATIONS:                                                    ║\n";
    for (plint iS = 0; iS < num_of_substrates; ++iS) {
        T sMin = computeMin(*computeDensity(vec_substr_lattices[iS]));
        T sMax = computeMax(*computeDensity(vec_substr_lattices[iS]));
        T sAvg = computeAverage(*computeDensity(vec_substr_lattices[iS]));
        pcout << "║   " << vec_subs_names[iS] << ": min=" << std::scientific << sMin
              << " avg=" << sAvg << " max=" << sMax << std::fixed << "\n";
    }
    pcout << "╚══════════════════════════════════════════════════════════════════════════╝\n";

    if (track_performance == 1) {
        pcout << "\n┌────────────────────────────────────────────────────────────────────────┐\n";
        pcout << "│ PERFORMANCE TIMING BREAKDOWN                                           │\n";
        pcout << "├────────────────────────────────────────────────────────────────────────┤\n";
        pcout << "│   NS (flow):         " << nstime << " s\n";
        pcout << "│   ADE (transport):   " << adetime << " s\n";
        pcout << "│   Collide+Stream:    " << cnstime << " s\n";
        if (ca_count > 0) pcout << "│   CA (biomass):      " << catime << " s\n";
        if (kns_count > 0) pcout << "│   Kinetics:          " << knstime << " s\n";
        if (useEquilibrium) pcout << "│   Equilibrium:       " << eqtime << " s\n";
        pcout << "└────────────────────────────────────────────────────────────────────────┘\n";
    }

    if (useEquilibrium) eqSolver.printStatistics();

    // Free allocated memory
    free(main_path);
    free(src_path);
    free(input_path);
    free(output_path);
    free(ns_filename);

    pcout << "\n╔══════════════════════════════════════════════════════════════════════════╗\n";
    pcout << "║                       Simulation Finished!                               ║\n";
    pcout << "║                                                                          ║\n";
    pcout << "║  Author:  Shahram Asgari                                                 ║\n";
    pcout << "║  Advisor: Dr. Christof Meile                                             ║\n";
    pcout << "║  Lab:     Meile Lab, University of Georgia                               ║\n";
    pcout << "╚══════════════════════════════════════════════════════════════════════════╝\n\n";

    return 0;
}
