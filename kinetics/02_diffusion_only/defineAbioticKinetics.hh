/* ============================================================================
 * defineAbioticKinetics.hh - NO-OP STUB (Diffusion Only)
 * CompLaB3D - University of Georgia
 *
 * Scenario: 02_diffusion_only
 *   Pure diffusion of a single tracer substrate with no flow and no
 *   abiotic reactions. The tracer spreads by molecular diffusion alone.
 *   This file is a no-op stub required because the solver unconditionally
 *   #includes defineAbioticKinetics.hh. All reaction rates are set to zero
 *   and the function returns immediately.
 *
 * Substrates: 1 (Tracer)
 * Reactions: None
 *
 * Usage:
 *   Copy this file to your simulation src/ directory when running a
 *   diffusion-only simulation with no abiotic kinetics.
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
// MAIN ABIOTIC KINETICS FUNCTION - NO-OP (Diffusion Only)
// ============================================================================
// Tracer diffuses but does not react. Zero all rates and return.
void defineAbioticRxnKinetics(
    std::vector<double> C,
    std::vector<double>& subsR,
    plb::plint mask
) {
    // Zero all substrate reaction rates
    for (size_t i = 0; i < subsR.size(); ++i) subsR[i] = 0.0;
    // No abiotic reactions in diffusion-only scenario
    return;
}

#endif // DEFINE_ABIOTIC_KINETICS_HH
