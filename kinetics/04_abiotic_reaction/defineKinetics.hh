/* ============================================================================
 * defineKinetics.hh - NO-OP STUB (Abiotic Reaction)
 * CompLaB3D - University of Georgia
 *
 * Scenario: 04_abiotic_reaction
 *   Abiotic first-order decay reaction A -> P. No biomass is involved;
 *   all chemistry is handled by the abiotic kinetics file.
 *   This file is a no-op stub required because the solver unconditionally
 *   #includes defineKinetics.hh. All reaction rates are set to zero and
 *   the function returns immediately.
 *
 * Substrates: 2 (Reactant A, Product P) -- handled by abiotic kinetics
 * Biomass species: 0
 * Biotic reactions: None
 *
 * Usage:
 *   Copy this file to your simulation src/ directory when running an
 *   abiotic-only reaction simulation with no biotic kinetics.
 * ============================================================================
 */
#ifndef DEFINE_KINETICS_HH
#define DEFINE_KINETICS_HH

#include <vector>
#include <cmath>
#include <algorithm>
#include <iostream>
#include <iomanip>

// ============================================================================
// KINETICS STATISTICS ACCUMULATOR (required by solver interface)
// ============================================================================
namespace KineticsStats {
    static double iter_sum_dB = 0.0;
    static double iter_sum_dDOC = 0.0;
    static double iter_max_biomass = 0.0;
    static double iter_max_dB = 0.0;
    static double iter_min_DOC = 1e30;
    static long iter_cells_with_biomass = 0;
    static long iter_cells_with_growth = 0;
    static long iter_total_calls = 0;
    static long iter_cells_limited = 0;

    inline void resetIteration() {
        iter_sum_dB = 0.0; iter_sum_dDOC = 0.0; iter_max_biomass = 0.0;
        iter_max_dB = 0.0; iter_min_DOC = 1e30;
        iter_cells_with_biomass = 0; iter_cells_with_growth = 0;
        iter_total_calls = 0; iter_cells_limited = 0;
    }
    inline void accumulate(double biomass, double DOC, double dB_dt, double dDOC_dt, bool was_limited) {
        iter_total_calls++;
        if (biomass > 0.1) {
            iter_cells_with_biomass++;
            iter_sum_dB += dB_dt; iter_sum_dDOC += dDOC_dt;
            if (biomass > iter_max_biomass) iter_max_biomass = biomass;
            if (dB_dt > iter_max_dB) iter_max_dB = dB_dt;
            if (DOC < iter_min_DOC && DOC > 0) iter_min_DOC = DOC;
            if (dB_dt > 0) iter_cells_with_growth++;
            if (was_limited) iter_cells_limited++;
        }
    }
    inline void accumulate(double biomass, double DOC, double dB_dt, double dDOC_dt) {
        accumulate(biomass, DOC, dB_dt, dDOC_dt, false);
    }
    inline void getStats(long& cells_biomass, long& cells_growth, double& sum_dB,
                         double& max_B, double& max_dB, double& min_DOC) {
        cells_biomass = iter_cells_with_biomass; cells_growth = iter_cells_with_growth;
        sum_dB = iter_sum_dB; max_B = iter_max_biomass; max_dB = iter_max_dB;
        min_DOC = (iter_min_DOC < 1e20) ? iter_min_DOC : 0.0;
    }
    inline long getLimitedCells() { return iter_cells_limited; }
}

// ============================================================================
// MAIN KINETICS FUNCTION - NO-OP (Abiotic Reaction)
// ============================================================================
// No biomass, no biotic reactions. All chemistry handled by abiotic kinetics.
// Zero all rates and return.
void defineRxnKinetics(
    std::vector<double> B,
    std::vector<double> C,
    std::vector<double>& subsR,
    std::vector<double>& bioR,
    plb::plint mask
) {
    // Zero all substrate reaction rates
    for (size_t i = 0; i < subsR.size(); ++i) subsR[i] = 0.0;
    // Zero all biomass reaction rates
    for (size_t i = 0; i < bioR.size(); ++i) bioR[i] = 0.0;
    // Biotic kinetics not used in this scenario
    return;
}

#endif // DEFINE_KINETICS_HH
