/* ============================================================================
 * defineAbioticKinetics_test2.hh - FIRST-ORDER DECAY
 * ============================================================================
 * TEST 2: First-Order Decay Reaction
 *
 * REACTION:
 *   A -> products
 *
 * RATE LAW:
 *   dA/dt = -k * [A]
 *
 * PARAMETERS:
 *   k = 1.0e-4 [1/s]  (decay rate constant)
 *
 * ANALYTICAL SOLUTION:
 *   [A](t) = [A]_0 * exp(-k*t)
 *
 * VALIDATION:
 *   Half-life t_1/2 = ln(2)/k = 6930 seconds
 *   At t = 6930 s: [A] = 0.5 * [A]_0
 *
 * TO USE THIS FILE:
 *   Copy this file to: src/defineAbioticKinetics.hh
 *   (or replace the function in the existing file)
 * ============================================================================
 */
#ifndef DEFINE_ABIOTIC_KINETICS_HH
#define DEFINE_ABIOTIC_KINETICS_HH

#include <vector>
#include <cmath>
#include <algorithm>
#include <iostream>
#include <iomanip>

namespace AbioticParams {
    // ========================================
    // TEST 2: First-Order Decay Parameters
    // ========================================
    constexpr double k_decay = 1.0e-4;    // [1/s] decay rate constant

    // Numerical stability
    constexpr double MIN_CONC = 1.0e-20;
    constexpr double MAX_RATE_FRACTION = 0.5;
    constexpr double dt_kinetics = 0.0075;
}

namespace AbioticKineticsStats {
    static long iter_total_calls = 0;
    static double iter_total_decay = 0.0;

    inline void resetIteration() {
        iter_total_calls = 0;
        iter_total_decay = 0.0;
    }

    inline void accumulate(double decay_rate) {
        iter_total_calls++;
        iter_total_decay += decay_rate;
    }

    inline void printStats(long iteration) {
        std::cout << "[ABIOTIC TEST2 iter=" << iteration << "] "
                  << "Cells=" << iter_total_calls
                  << " TotalDecay=" << std::scientific << iter_total_decay
                  << std::fixed << "\n";
    }
}

/* ============================================================================
 * MAIN KINETICS FUNCTION - TEST 2: First-Order Decay
 * ============================================================================
 */
void defineAbioticRxnKinetics(
    std::vector<double> C,           // Input: concentrations [mol/L]
    std::vector<double>& subsR,      // Output: rates [mol/L/s]
    plb::plint mask                  // Cell type
) {
    using namespace AbioticParams;

    // Initialize all rates to zero
    for (size_t i = 0; i < subsR.size(); ++i) {
        subsR[i] = 0.0;
    }

    // ========================================
    // FIRST-ORDER DECAY: A -> products
    // Rate: dA/dt = -k * [A]
    // ========================================

    if (C.size() >= 1) {
        double A = std::max(C[0], MIN_CONC);

        // Calculate decay rate
        double dA_dt = -k_decay * A;

        // Stability clamp: don't consume more than 50% per timestep
        double max_rate = A * MAX_RATE_FRACTION / dt_kinetics;
        if (-dA_dt > max_rate) {
            dA_dt = -max_rate;
        }

        // Set output rate
        subsR[0] = dA_dt;

        // Statistics
        AbioticKineticsStats::accumulate(-dA_dt);
    }

    // Output validation
    for (size_t i = 0; i < subsR.size(); ++i) {
        if (std::isnan(subsR[i]) || std::isinf(subsR[i])) {
            std::cerr << "[ERROR] NaN/Inf in abiotic kinetics!\n";
            subsR[i] = 0.0;
        }
    }
}

namespace AbioticKineticsValidation {
    inline bool validateParameters() {
        using namespace AbioticParams;

        std::cout << "\n";
        std::cout << "============================================================\n";
        std::cout << "  TEST 2: FIRST-ORDER DECAY VALIDATION\n";
        std::cout << "============================================================\n";
        std::cout << "  Reaction: A -> products\n";
        std::cout << "  Rate law: dA/dt = -k * [A]\n";
        std::cout << "  k_decay = " << std::scientific << k_decay << " [1/s]\n";
        std::cout << "  Half-life = " << std::fixed << std::setprecision(1)
                  << (0.693147 / k_decay) << " seconds\n";
        std::cout << "============================================================\n\n";

        return (k_decay > 0);
    }
}

#endif // DEFINE_ABIOTIC_KINETICS_HH
