/* ============================================================================
 * defineAbioticKinetics.hh - Scenario 09: Coupled Biotic + Abiotic Reactions
 * CompLaB3D - University of Georgia
 *
 * First-order abiotic decay of the Byproduct produced by biofilm metabolism.
 * DOC is NOT modified by abiotic reactions (only consumed biotically).
 *
 * SPECIES MAPPING:
 *   C[0] = DOC (dissolved organic carbon) [mol/L]  -- not touched here
 *   C[1] = Byproduct [mol/L]                       -- decays abiotically
 *
 * ABIOTIC REACTION:
 *   dDOC/dt       = 0                        (no abiotic DOC reaction)
 *   dByproduct/dt = -k_decay * [Byproduct]   (first-order decay)
 *
 * The solver sums biotic rates (from defineKinetics.hh) and abiotic rates
 * (from this file) for each substrate, so the total Byproduct rate is:
 *   dByproduct/dt_total = (biotic production) + (-k_decay * [Byproduct])
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
// ABIOTIC KINETIC PARAMETERS
// ============================================================================
namespace AbioticParams {
    constexpr double k_decay = 1.0e-5;    // [1/s] first-order decay rate for Byproduct
    constexpr double MIN_CONC = 1.0e-20;   // [mol/L] minimum concentration threshold
}

// ============================================================================
// ABIOTIC KINETICS STATISTICS
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
// ABIOTIC KINETICS FUNCTION
// ============================================================================
void defineAbioticRxnKinetics(
    std::vector<double> C,
    std::vector<double>& subsR,
    plb::plint mask
) {
    // Initialize all rates to zero
    for (size_t i = 0; i < subsR.size(); ++i) {
        subsR[i] = 0.0;
    }

    // subsR[0] = 0.0 -- DOC is not modified by abiotic reactions

    // First-order decay of Byproduct: dByproduct/dt = -k * [Byproduct]
    if (C.size() > 1 && C[1] > AbioticParams::MIN_CONC) {
        double byproduct = C[1];
        double dByproduct_dt = -AbioticParams::k_decay * byproduct;

        if (subsR.size() > 1) subsR[1] = dByproduct_dt;

        // Track statistics
        AbioticKineticsStats::accumulate(dByproduct_dt);
    }
}

#endif // DEFINE_ABIOTIC_KINETICS_HH
