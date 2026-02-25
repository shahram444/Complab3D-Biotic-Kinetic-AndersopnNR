/* ============================================================================
 * defineAbioticKinetics.hh - FIRST-ORDER DECAY A -> P
 * CompLaB3D - University of Georgia
 *
 * Scenario: 04_abiotic_reaction
 *   First-order abiotic decay of Reactant A into Product P.
 *   No biomass is involved; this is a purely chemical transformation.
 *
 *   Reaction: A -> P
 *   Rate law: dA/dt = -k_decay * [A]
 *             dP/dt = +k_decay * [A]
 *
 * Substrates:
 *   C[0] = Reactant A  [mol/L]
 *   C[1] = Product P    [mol/L]
 *
 * Parameters:
 *   k_decay    = 1e-5 [1/s]  first-order decay rate constant
 *   MAX_FRAC   = 0.5         max fraction consumed per timestep (stability)
 *   dt         = 0.0075 [s]  kinetics timestep
 *
 * Usage:
 *   Copy this file to your simulation src/ directory when running an
 *   abiotic first-order decay simulation.
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
    constexpr double k_decay    = 1.0e-5;   // [1/s] first-order decay rate
    constexpr double MIN_CONC   = 1.0e-20;  // [mol/L] minimum concentration floor
    constexpr double MAX_FRAC   = 0.5;      // max fraction consumed per timestep
    constexpr double dt         = 0.0075;    // [s] kinetics timestep
}

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
// MAIN ABIOTIC KINETICS FUNCTION - FIRST-ORDER DECAY A -> P
// ============================================================================
/*
 * defineAbioticRxnKinetics - First-order decay of Reactant into Product
 *
 * INPUTS:
 *   C[0]  = Reactant A concentration [mol/L]
 *   C[1]  = Product P concentration  [mol/L]
 *   mask  = cell type identifier
 *
 * OUTPUTS:
 *   subsR[0] = dA/dt  (negative, consumption)
 *   subsR[1] = dP/dt  (positive, production)
 */
void defineAbioticRxnKinetics(
    std::vector<double> C,
    std::vector<double>& subsR,
    plb::plint mask
) {
    using namespace AbioticParams;

    // Initialize all rates to zero
    for (size_t i = 0; i < subsR.size(); ++i) {
        subsR[i] = 0.0;
    }

    // Need at least 2 substrates: Reactant (C[0]) and Product (C[1])
    if (C.size() < 2 || subsR.size() < 2) return;

    // Get reactant concentration (floor at MIN_CONC)
    double A = std::max(C[0], 0.0);
    if (A < MIN_CONC) return;

    // ========================================================================
    // First-order decay: dA/dt = -k_decay * A
    // ========================================================================
    double rate = k_decay * A;

    // Stability clamping: do not consume more than MAX_FRAC of A per timestep
    double max_rate = A * MAX_FRAC / dt;
    if (rate > max_rate) {
        rate = max_rate;
    }

    // Set reaction rates: A consumed, P produced (stoichiometry 1:1)
    subsR[0] = -rate;   // Reactant consumed
    subsR[1] = +rate;   // Product produced

    // Track statistics
    AbioticKineticsStats::accumulate(-rate);

    // Output validation
    if (std::isnan(rate) || std::isinf(rate)) {
        std::cerr << "[ABIOTIC KINETICS ERROR] NaN/Inf in decay rate! A=" << C[0] << "\n";
        subsR[0] = 0.0;
        subsR[1] = 0.0;
    }
}

#endif // DEFINE_ABIOTIC_KINETICS_HH
