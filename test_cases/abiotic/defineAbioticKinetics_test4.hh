/* ============================================================================
 * defineAbioticKinetics_test4.hh - REVERSIBLE REACTION
 * ============================================================================
 * TEST 4: Reversible First-Order Reaction
 *
 * REACTION:
 *   A <-> B (reversible)
 *   Forward: A -> B with k_f
 *   Reverse: B -> A with k_r
 *
 * RATE LAW:
 *   dA/dt = -k_f * [A] + k_r * [B]
 *   dB/dt = +k_f * [A] - k_r * [B]
 *
 * PARAMETERS:
 *   k_f = 1.0e-3 [1/s]  (forward rate)
 *   k_r = 5.0e-4 [1/s]  (reverse rate)
 *
 * EQUILIBRIUM:
 *   K_eq = k_f / k_r = 2.0
 *   At equilibrium: [B]/[A] = 2.0
 *
 * INITIAL CONDITIONS:
 *   [A]_0 = 1.0 mol/L, [B]_0 = 0.0 mol/L
 *
 * VALIDATION:
 *   Conservation: [A] + [B] = 1.0 mol/L (constant)
 *   Equilibrium: [A]_eq = 0.333, [B]_eq = 0.667 mol/L
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
    // TEST 4: Reversible Reaction Parameters
    // ========================================
    constexpr double k_forward = 1.0e-3;  // [1/s] forward rate A -> B
    constexpr double k_reverse = 5.0e-4;  // [1/s] reverse rate B -> A

    // Derived: K_eq = k_f/k_r = 2.0

    // Numerical stability
    constexpr double MIN_CONC = 1.0e-20;
    constexpr double MAX_RATE_FRACTION = 0.3;
    constexpr double dt_kinetics = 0.0075;
}

namespace AbioticKineticsStats {
    static long iter_total_calls = 0;
    static double iter_sum_A = 0.0;
    static double iter_sum_B = 0.0;

    inline void resetIteration() {
        iter_total_calls = 0;
        iter_sum_A = 0.0;
        iter_sum_B = 0.0;
    }

    inline void accumulate(double A, double B) {
        iter_total_calls++;
        iter_sum_A += A;
        iter_sum_B += B;
    }

    inline void printStats(long iteration) {
        if (iter_total_calls > 0) {
            double avg_A = iter_sum_A / iter_total_calls;
            double avg_B = iter_sum_B / iter_total_calls;
            double total = avg_A + avg_B;
            double ratio = (avg_A > 1e-10) ? avg_B / avg_A : 0.0;

            std::cout << "[ABIOTIC TEST4 iter=" << iteration << "] "
                      << "Avg: A=" << std::fixed << std::setprecision(4) << avg_A
                      << " B=" << avg_B
                      << " Total=" << total << " (should be 1.0)"
                      << " B/A=" << std::setprecision(2) << ratio
                      << " (K_eq=2.0)\n";
        }
    }
}

/* ============================================================================
 * MAIN KINETICS FUNCTION - TEST 4: Reversible Reaction A <-> B
 * ============================================================================
 */
void defineAbioticRxnKinetics(
    std::vector<double> C,           // Input: [A, B] concentrations [mol/L]
    std::vector<double>& subsR,      // Output: rates [mol/L/s]
    plb::plint mask                  // Cell type
) {
    using namespace AbioticParams;

    // Initialize all rates to zero
    for (size_t i = 0; i < subsR.size(); ++i) {
        subsR[i] = 0.0;
    }

    // ========================================
    // REVERSIBLE REACTION: A <-> B
    // Forward: A -> B, rate = k_f * [A]
    // Reverse: B -> A, rate = k_r * [B]
    // ========================================

    if (C.size() >= 2) {
        double A = std::max(C[0], MIN_CONC);
        double B = std::max(C[1], MIN_CONC);

        // Calculate forward and reverse rates
        double forward_rate = k_forward * A;
        double reverse_rate = k_reverse * B;

        // Net rate (positive = A decreasing, B increasing)
        double net_rate = forward_rate - reverse_rate;

        // Stability clamp
        double max_rate_A = A * MAX_RATE_FRACTION / dt_kinetics;
        double max_rate_B = B * MAX_RATE_FRACTION / dt_kinetics;

        if (net_rate > 0 && net_rate > max_rate_A) {
            net_rate = max_rate_A;
        }
        if (net_rate < 0 && -net_rate > max_rate_B) {
            net_rate = -max_rate_B;
        }

        // Set rates
        subsR[0] = -net_rate;  // A: consumed if net_rate > 0, produced if < 0
        subsR[1] = +net_rate;  // B: produced if net_rate > 0, consumed if < 0

        // Statistics
        AbioticKineticsStats::accumulate(C[0], C[1]);
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

        double K_eq = k_forward / k_reverse;
        double A_eq = 1.0 / (1.0 + K_eq);
        double B_eq = K_eq / (1.0 + K_eq);

        std::cout << "\n";
        std::cout << "============================================================\n";
        std::cout << "  TEST 4: REVERSIBLE REACTION VALIDATION\n";
        std::cout << "============================================================\n";
        std::cout << "  Reaction: A <-> B\n";
        std::cout << "  Forward: k_f = " << std::scientific << k_forward << " [1/s]\n";
        std::cout << "  Reverse: k_r = " << k_reverse << " [1/s]\n";
        std::cout << "  K_eq = k_f/k_r = " << std::fixed << std::setprecision(2) << K_eq << "\n";
        std::cout << "  Initial: [A]=1.0, [B]=0.0 mol/L\n";
        std::cout << "  Expected equilibrium:\n";
        std::cout << "    [A]_eq = " << std::setprecision(4) << A_eq << " mol/L\n";
        std::cout << "    [B]_eq = " << B_eq << " mol/L\n";
        std::cout << "  Conservation: [A]+[B] = 1.0 mol/L\n";
        std::cout << "============================================================\n\n";

        return (k_forward > 0 && k_reverse > 0);
    }
}

#endif // DEFINE_ABIOTIC_KINETICS_HH
