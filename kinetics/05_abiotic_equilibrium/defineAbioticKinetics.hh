/* ============================================================================
 * defineAbioticKinetics.hh - NO-OP STUB (Abiotic Equilibrium)
 * CompLaB3D - University of Georgia
 *
 * Scenario: 05_abiotic_equilibrium
 *   Equilibrium speciation of carbonate system species. ALL speciation
 *   chemistry is handled by the equilibrium solver, NOT by kinetic rate
 *   expressions in this file. This function explicitly sets all kinetic
 *   rates to zero and returns immediately.
 *
 * Substrates (5 total, managed by equilibrium solver):
 *   C[0] = DOC   (dissolved organic carbon)  [mol/L]
 *   C[1] = CO2   (dissolved carbon dioxide)  [mol/L]
 *   C[2] = HCO3  (bicarbonate)               [mol/L]
 *   C[3] = CO3   (carbonate)                 [mol/L]
 *   C[4] = H+    (hydrogen ion / pH)         [mol/L]
 *
 * Kinetic reactions: None (all rates = 0)
 *
 * Usage:
 *   Copy this file to your simulation src/ directory when running an
 *   equilibrium speciation simulation. The equilibrium solver handles
 *   all interconversion between carbonate species.
 * ============================================================================
 */
#ifndef DEFINE_ABIOTIC_KINETICS_HH
#define DEFINE_ABIOTIC_KINETICS_HH

#include <vector>
#include <cmath>
#include <algorithm>
#include <iostream>
#include <iomanip>

// ============================================================================
// ABIOTIC KINETICS STATISTICS (required by solver interface)
// ============================================================================
namespace AbioticKineticsStats {
    static double iter_total_reaction = 0.0;
    static long iter_cells_reacting = 0;
    static long iter_total_calls = 0;
    inline void resetIteration() {
        iter_total_reaction = 0.0; iter_cells_reacting = 0; iter_total_calls = 0;
    }
    inline void accumulate(double total_rate) {
        iter_total_calls++;
        if (std::abs(total_rate) > 1e-20) { iter_cells_reacting++; iter_total_reaction += total_rate; }
    }
}

// ============================================================================
// MAIN ABIOTIC KINETICS FUNCTION - NO-OP (Equilibrium Solver Handles All)
// ============================================================================
/*
 * defineAbioticRxnKinetics - All kinetic rates are zero.
 *
 * The equilibrium solver manages speciation of:
 *   DOC, CO2, HCO3, CO3, H+
 * No kinetic rate expressions are needed here.
 *
 * INPUTS:
 *   C[0..4] = Substrate concentrations [mol/L]
 *   mask    = cell type identifier
 *
 * OUTPUTS:
 *   subsR[0..4] = all set to 0.0 (no kinetic reactions)
 */
void defineAbioticRxnKinetics(
    std::vector<double> C,
    std::vector<double>& subsR,
    plb::plint mask
) {
    // Zero ALL substrate reaction rates -- equilibrium solver handles speciation
    for (size_t i = 0; i < subsR.size(); ++i) {
        subsR[i] = 0.0;
    }
    // No kinetic reactions in equilibrium scenario
    return;
}

#endif // DEFINE_ABIOTIC_KINETICS_HH
