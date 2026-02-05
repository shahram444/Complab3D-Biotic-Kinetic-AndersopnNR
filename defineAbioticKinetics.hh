/* ============================================================================
 * defineAbioticKinetics.hh - ABIOTIC KINETICS (NO MICROBES)
 * CompLaB3D - University of Georgia
 *
 * This file defines chemical reactions between substrates WITHOUT biomass.
 * Examples:
 *   - First-order decay: dC/dt = -k * C
 *   - Bimolecular: A + B → C with dC/dt = k * [A] * [B]
 *   - Radioactive decay
 *   - Photo-degradation
 *   - Chemical oxidation/reduction
 *
 * HOW TO USE:
 *   1. Set enable_abiotic_kinetics=true in XML
 *   2. Modify the defineAbioticRxnKinetics() function below
 *   3. Set reaction rate constants in AbioticParams namespace
 *
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
// Modify these parameters for your specific reactions
namespace AbioticParams {
    // Example: First-order decay rate for substrate 0
    constexpr double k_decay_0 = 1.0e-5;   // [1/s] first-order decay rate

    // Example: Second-order reaction rate A + B → C
    constexpr double k_reaction = 1.0e-3;  // [L/mol/s] or [1/(mol/L)/s]

    // Numerical stability
    constexpr double MIN_CONC = 1.0e-20;
    constexpr double MAX_RATE_FRACTION = 0.5;  // Max fraction of species that can react per timestep
    constexpr double dt_kinetics = 0.0075;     // [s] timestep
}

// ============================================================================
// ABIOTIC KINETICS STATISTICS
// ============================================================================
namespace AbioticKineticsStats {
    static double iter_total_reaction = 0.0;
    static long iter_cells_reacting = 0;
    static long iter_total_calls = 0;

    inline void resetIteration() {
        iter_total_reaction = 0.0;
        iter_cells_reacting = 0;
        iter_total_calls = 0;
    }

    inline void accumulate(double total_rate) {
        iter_total_calls++;
        if (std::abs(total_rate) > 1e-20) {
            iter_cells_reacting++;
            iter_total_reaction += total_rate;
        }
    }

    inline void printStats() {
        std::cout << "[ABIOTIC] Cells: " << iter_total_calls
                  << " Reacting: " << iter_cells_reacting
                  << " Total rate: " << std::scientific << iter_total_reaction
                  << std::fixed << "\n";
    }
}

// ============================================================================
// MAIN ABIOTIC KINETICS FUNCTION
// ============================================================================
/*
 * defineAbioticRxnKinetics - Calculate reaction rates for substrate-only reactions
 *
 * INPUTS:
 *   C      = vector of substrate concentrations [mol/L]
 *   mask   = cell type (for spatially-dependent reactions)
 *
 * OUTPUTS:
 *   subsR  = vector of reaction rates for each substrate [mol/L/s]
 *            Negative = consumption, Positive = production
 *
 * MODIFY THIS FUNCTION FOR YOUR SPECIFIC REACTIONS!
 */
void defineAbioticRxnKinetics(
    std::vector<double> C,           // Substrate concentrations [mol/L]
    std::vector<double>& subsR,      // Reaction rates [mol/L/s] (output)
    plb::plint mask                  // Cell type
) {
    using namespace AbioticParams;

    // Initialize all rates to zero
    for (size_t i = 0; i < subsR.size(); ++i) {
        subsR[i] = 0.0;
    }

    // ========================================================================
    // EXAMPLE 1: First-order decay of substrate 0
    // Reaction: A → products
    // Rate law: dA/dt = -k * [A]
    // ========================================================================
    if (C.size() > 0) {
        double A = std::max(C[0], MIN_CONC);

        // First-order decay
        double dA_dt = -k_decay_0 * A;

        // Clamp to prevent negative concentrations
        double max_rate = A * MAX_RATE_FRACTION / dt_kinetics;
        if (-dA_dt > max_rate) {
            dA_dt = -max_rate;
        }

        subsR[0] = dA_dt;

        // Track statistics
        AbioticKineticsStats::accumulate(dA_dt);
    }

    // ========================================================================
    // EXAMPLE 2: Bimolecular reaction A + B → C
    // Rate law: dA/dt = dB/dt = -k*[A]*[B], dC/dt = +k*[A]*[B]
    // Uncomment to enable
    // ========================================================================
    /*
    if (C.size() >= 3) {
        double A = std::max(C[0], MIN_CONC);
        double B = std::max(C[1], MIN_CONC);

        // Bimolecular reaction rate
        double rate = k_reaction * A * B;

        // Clamp to prevent negative concentrations
        double max_rate_A = A * MAX_RATE_FRACTION / dt_kinetics;
        double max_rate_B = B * MAX_RATE_FRACTION / dt_kinetics;
        double max_rate = std::min(max_rate_A, max_rate_B);

        if (rate > max_rate) {
            rate = max_rate;
        }

        // A consumed
        subsR[0] = -rate;
        // B consumed
        subsR[1] = -rate;
        // C produced
        subsR[2] = +rate;
    }
    */

    // ========================================================================
    // EXAMPLE 3: Reversible reaction A ⇌ B (with equilibrium tendency)
    // Forward: A → B with k_f
    // Reverse: B → A with k_r
    // At equilibrium: K_eq = k_f/k_r = [B]/[A]
    // Uncomment to enable
    // ========================================================================
    /*
    if (C.size() >= 2) {
        double A = std::max(C[0], MIN_CONC);
        double B = std::max(C[1], MIN_CONC);

        constexpr double k_forward = 1.0e-4;  // [1/s]
        constexpr double k_reverse = 1.0e-5;  // [1/s]

        double forward_rate = k_forward * A;
        double reverse_rate = k_reverse * B;
        double net_rate = forward_rate - reverse_rate;

        // Clamp
        double max_rate_A = A * MAX_RATE_FRACTION / dt_kinetics;
        double max_rate_B = B * MAX_RATE_FRACTION / dt_kinetics;

        if (net_rate > 0 && net_rate > max_rate_A) net_rate = max_rate_A;
        if (net_rate < 0 && -net_rate > max_rate_B) net_rate = -max_rate_B;

        subsR[0] = -net_rate;  // A consumed (or produced if reverse dominates)
        subsR[1] = +net_rate;  // B produced (or consumed if reverse dominates)
    }
    */

    // ========================================================================
    // ADD YOUR CUSTOM REACTIONS HERE
    // ========================================================================
    // Remember:
    //   - C[i] = concentration of substrate i
    //   - subsR[i] = rate of change for substrate i [mol/L/s]
    //   - Negative rate = consumption
    //   - Positive rate = production
    //   - Always clamp rates to prevent instability
    // ========================================================================

    // Output validation
    for (size_t i = 0; i < subsR.size(); ++i) {
        if (std::isnan(subsR[i]) || std::isinf(subsR[i])) {
            std::cerr << "[ABIOTIC KINETICS ERROR] NaN/Inf in rate for substrate " << i << "\n";
            subsR[i] = 0.0;
        }
    }
}

// ============================================================================
// VALIDATION FUNCTION - Call at startup
// ============================================================================
namespace AbioticKineticsValidation {

    inline bool validateParameters() {
        using namespace AbioticParams;
        bool all_ok = true;

        std::cout << "\n";
        std::cout << "╔══════════════════════════════════════════════════════════════════════╗\n";
        std::cout << "║           ABIOTIC KINETICS PARAMETER VALIDATION                      ║\n";
        std::cout << "╠══════════════════════════════════════════════════════════════════════╣\n";

        std::cout << "║ k_decay_0  = " << std::scientific << k_decay_0 << " [1/s]   ";
        if (k_decay_0 >= 0) {
            std::cout << "✓ OK\n";
        } else {
            std::cout << "✗ FAIL: Negative rate!\n";
            all_ok = false;
        }

        std::cout << "║ k_reaction = " << std::scientific << k_reaction << " [L/mol/s]";
        if (k_reaction >= 0) {
            std::cout << "✓ OK\n";
        } else {
            std::cout << "✗ FAIL: Negative rate!\n";
            all_ok = false;
        }

        std::cout << "║ dt_kinetics= " << std::scientific << dt_kinetics << " [s]     ";
        if (dt_kinetics > 0) {
            std::cout << "✓ OK\n";
        } else {
            std::cout << "✗ FAIL: Invalid timestep!\n";
            all_ok = false;
        }

        std::cout << "╠══════════════════════════════════════════════════════════════════════╣\n";
        if (all_ok) {
            std::cout << "║ ABIOTIC KINETICS: ✓ PARAMETERS OK                                   ║\n";
        } else {
            std::cout << "║ ABIOTIC KINETICS: ✗ ERRORS FOUND!                                   ║\n";
        }
        std::cout << "╚══════════════════════════════════════════════════════════════════════╝\n\n";

        return all_ok;
    }
}

#endif // DEFINE_ABIOTIC_KINETICS_HH
