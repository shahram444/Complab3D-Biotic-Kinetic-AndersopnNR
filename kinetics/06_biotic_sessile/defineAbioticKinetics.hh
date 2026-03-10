/* ============================================================================
 * defineAbioticKinetics.hh - Scenario 06: Single Sessile Biofilm (CA Solver)
 * CompLaB3D - University of Georgia
 *
 * NO-OP STUB: This scenario has no abiotic reactions.
 * All substrate transformations are handled by biotic kinetics
 * (defineKinetics.hh). This file is included unconditionally by the solver
 * and must provide the required function signature and statistics namespace.
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
// ABIOTIC KINETICS FUNCTION (no-op stub)
// ============================================================================
void defineAbioticRxnKinetics(
    std::vector<double> C,
    std::vector<double>& subsR,
    plb::plint mask
) {
    // Zero all rates -- no abiotic reactions in this scenario
    for (size_t i = 0; i < subsR.size(); ++i) {
        subsR[i] = 0.0;
    }
}

#endif // DEFINE_ABIOTIC_KINETICS_HH
