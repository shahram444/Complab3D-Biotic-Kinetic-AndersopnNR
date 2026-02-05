/* ============================================================================
 * defineAbioticKinetics_test3.hh - BIMOLECULAR REACTION
 * ============================================================================
 * TEST 3: Bimolecular Reaction
 *
 * REACTION:
 *   A + B -> C
 *
 * RATE LAW:
 *   dA/dt = -k * [A] * [B]
 *   dB/dt = -k * [A] * [B]
 *   dC/dt = +k * [A] * [B]
 *
 * PARAMETERS:
 *   k = 1.0e-2 [L/mol/s]  (second-order rate constant)
 *
 * INITIAL CONDITIONS:
 *   [A]_0 = 1.0 mol/L
 *   [B]_0 = 0.5 mol/L (limiting reagent)
 *   [C]_0 = 0.0 mol/L
 *
 * VALIDATION:
 *   At completion: [A]=0.5, [B]=0, [C]=0.5 mol/L
 *   Mass balance: [A]+[B]+[C] = 1.5 mol/L (constant)
 *
 * TO USE THIS FILE:
 *   Copy this file to: src/defineAbioticKinetics.hh
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
    // TEST 3: Bimolecular Reaction Parameters
    // ========================================
    constexpr double k_bimol = 1.0e-2;    // [L/mol/s] second-order rate constant

    // Numerical stability
    constexpr double MIN_CONC = 1.0e-20;
    constexpr double MAX_RATE_FRACTION = 0.3;  // More conservative for bimolecular
    constexpr double dt_kinetics = 0.0075;
}

namespace AbioticKineticsStats {
    static long iter_total_calls = 0;
    static double iter_sum_A = 0.0;
    static double iter_sum_B = 0.0;
    static double iter_sum_C = 0.0;

    inline void resetIteration() {
        iter_total_calls = 0;
        iter_sum_A = 0.0;
        iter_sum_B = 0.0;
        iter_sum_C = 0.0;
    }

    inline void accumulate(double A, double B, double C) {
        iter_total_calls++;
        iter_sum_A += A;
        iter_sum_B += B;
        iter_sum_C += C;
    }

    inline void printStats(long iteration) {
        if (iter_total_calls > 0) {
            double avg_A = iter_sum_A / iter_total_calls;
            double avg_B = iter_sum_B / iter_total_calls;
            double avg_C = iter_sum_C / iter_total_calls;
            double total = avg_A + avg_B + avg_C;

            std::cout << "[ABIOTIC TEST3 iter=" << iteration << "] "
                      << "Avg: A=" << std::fixed << std::setprecision(4) << avg_A
                      << " B=" << avg_B
                      << " C=" << avg_C
                      << " Total=" << total << " (should be 1.5)\n";
        }
    }
}

/* ============================================================================
 * MAIN KINETICS FUNCTION - TEST 3: Bimolecular Reaction A + B -> C
 * ============================================================================
 */
void defineAbioticRxnKinetics(
    std::vector<double> C,           // Input: [A, B, C] concentrations [mol/L]
    std::vector<double>& subsR,      // Output: rates [mol/L/s]
    plb::plint mask                  // Cell type
) {
    using namespace AbioticParams;

    // Initialize all rates to zero
    for (size_t i = 0; i < subsR.size(); ++i) {
        subsR[i] = 0.0;
    }

    // ========================================
    // BIMOLECULAR REACTION: A + B -> C
    // Rate: r = k * [A] * [B]
    // ========================================

    if (C.size() >= 3) {
        double A = std::max(C[0], MIN_CONC);
        double B = std::max(C[1], MIN_CONC);
        // C[2] is product C

        // Calculate reaction rate
        double rate = k_bimol * A * B;

        // Stability clamp: limit by limiting reagent
        double max_rate_A = A * MAX_RATE_FRACTION / dt_kinetics;
        double max_rate_B = B * MAX_RATE_FRACTION / dt_kinetics;
        double max_rate = std::min(max_rate_A, max_rate_B);

        if (rate > max_rate) {
            rate = max_rate;
        }

        // Stoichiometry: A + B -> C (1:1:1)
        subsR[0] = -rate;  // A consumed
        subsR[1] = -rate;  // B consumed
        subsR[2] = +rate;  // C produced

        // Statistics for validation
        AbioticKineticsStats::accumulate(C[0], C[1], C[2]);
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
        std::cout << "  TEST 3: BIMOLECULAR REACTION VALIDATION\n";
        std::cout << "============================================================\n";
        std::cout << "  Reaction: A + B -> C\n";
        std::cout << "  Rate law: r = k * [A] * [B]\n";
        std::cout << "  k_bimol = " << std::scientific << k_bimol << " [L/mol/s]\n";
        std::cout << "  Initial: [A]=1.0, [B]=0.5, [C]=0.0 mol/L\n";
        std::cout << "  Expected final: [A]=0.5, [B]=0, [C]=0.5 mol/L\n";
        std::cout << "  Mass balance: [A]+[B]+[C] = 1.5 mol/L (constant)\n";
        std::cout << "============================================================\n\n";

        return (k_bimol > 0);
    }
}

#endif // DEFINE_ABIOTIC_KINETICS_HH
