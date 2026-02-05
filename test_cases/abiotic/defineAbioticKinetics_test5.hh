/* ============================================================================
 * defineAbioticKinetics_test5.hh - SEQUENTIAL DECAY CHAIN
 * ============================================================================
 * TEST 5: Sequential Decay Chain (Radioactive Decay Series)
 *
 * REACTIONS:
 *   A -> B with k1  (parent decays to daughter)
 *   B -> C with k2  (daughter decays to granddaughter)
 *
 * RATE LAWS:
 *   dA/dt = -k1 * [A]
 *   dB/dt = +k1 * [A] - k2 * [B]
 *   dC/dt = +k2 * [B]
 *
 * PARAMETERS:
 *   k1 = 2.0e-4 [1/s]  (A -> B)
 *   k2 = 1.0e-4 [1/s]  (B -> C)
 *
 * INITIAL CONDITIONS:
 *   [A]_0 = 1.0, [B]_0 = 0.0, [C]_0 = 0.0 mol/L
 *
 * VALIDATION:
 *   Mass balance: [A]+[B]+[C] = 1.0 mol/L (constant)
 *   Final state: [A]=0, [B]=0, [C]=1.0 mol/L
 *   B shows transient peak before decaying
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
    // TEST 5: Decay Chain Parameters
    // ========================================
    constexpr double k1 = 2.0e-4;  // [1/s] A -> B decay rate
    constexpr double k2 = 1.0e-4;  // [1/s] B -> C decay rate

    // Half-lives
    // t_1/2(A) = ln(2)/k1 = 3466 s
    // t_1/2(B) = ln(2)/k2 = 6932 s

    // Numerical stability
    constexpr double MIN_CONC = 1.0e-20;
    constexpr double MAX_RATE_FRACTION = 0.3;
    constexpr double dt_kinetics = 0.0075;
}

namespace AbioticKineticsStats {
    static long iter_total_calls = 0;
    static double iter_sum_A = 0.0;
    static double iter_sum_B = 0.0;
    static double iter_sum_C = 0.0;
    static double iter_max_B = 0.0;  // Track peak of B

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
        if (B > iter_max_B) iter_max_B = B;
    }

    inline void printStats(long iteration) {
        if (iter_total_calls > 0) {
            double avg_A = iter_sum_A / iter_total_calls;
            double avg_B = iter_sum_B / iter_total_calls;
            double avg_C = iter_sum_C / iter_total_calls;
            double total = avg_A + avg_B + avg_C;

            std::cout << "[ABIOTIC TEST5 iter=" << iteration << "] "
                      << "A=" << std::fixed << std::setprecision(4) << avg_A
                      << " B=" << avg_B
                      << " C=" << avg_C
                      << " Total=" << total
                      << " B_max=" << iter_max_B << "\n";
        }
    }
}

/* ============================================================================
 * MAIN KINETICS FUNCTION - TEST 5: Decay Chain A -> B -> C
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
    // DECAY CHAIN: A -> B -> C
    // ========================================

    if (C.size() >= 3) {
        double A = std::max(C[0], MIN_CONC);
        double B = std::max(C[1], MIN_CONC);
        // C[2] is product C

        // Calculate individual decay rates
        double rate_A_to_B = k1 * A;  // A decaying to B
        double rate_B_to_C = k2 * B;  // B decaying to C

        // Stability clamp for A -> B
        double max_rate_A = A * MAX_RATE_FRACTION / dt_kinetics;
        if (rate_A_to_B > max_rate_A) {
            rate_A_to_B = max_rate_A;
        }

        // Stability clamp for B -> C
        double max_rate_B = B * MAX_RATE_FRACTION / dt_kinetics;
        if (rate_B_to_C > max_rate_B) {
            rate_B_to_C = max_rate_B;
        }

        // Set rates according to reaction network:
        // A: only decays (source of B)
        // B: produced from A, consumed to C
        // C: only produced from B

        subsR[0] = -rate_A_to_B;                    // A decreases
        subsR[1] = +rate_A_to_B - rate_B_to_C;     // B: gain from A, loss to C
        subsR[2] = +rate_B_to_C;                    // C increases

        // Statistics
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

        double t_half_A = 0.693147 / k1;
        double t_half_B = 0.693147 / k2;

        // Time when B reaches maximum (from Bateman equations)
        double t_max_B = std::log(k1/k2) / (k1 - k2);
        double B_max = std::exp(-k2 * t_max_B) - std::exp(-k1 * t_max_B);
        B_max *= k1 / (k2 - k1);

        std::cout << "\n";
        std::cout << "============================================================\n";
        std::cout << "  TEST 5: SEQUENTIAL DECAY CHAIN VALIDATION\n";
        std::cout << "============================================================\n";
        std::cout << "  Reactions: A -> B -> C\n";
        std::cout << "  k1 (A->B) = " << std::scientific << k1 << " [1/s]\n";
        std::cout << "  k2 (B->C) = " << k2 << " [1/s]\n";
        std::cout << "  Half-life A = " << std::fixed << std::setprecision(1) << t_half_A << " s\n";
        std::cout << "  Half-life B = " << t_half_B << " s\n";
        std::cout << "  Initial: [A]=1.0, [B]=0.0, [C]=0.0 mol/L\n";
        std::cout << "  B reaches max at t = " << t_max_B << " s\n";
        std::cout << "  B_max = " << std::setprecision(4) << B_max << " mol/L\n";
        std::cout << "  Final state: [A]=0, [B]=0, [C]=1.0 mol/L\n";
        std::cout << "  Conservation: [A]+[B]+[C] = 1.0 mol/L\n";
        std::cout << "============================================================\n\n";

        return (k1 > 0 && k2 > 0);
    }
}

#endif // DEFINE_ABIOTIC_KINETICS_HH
