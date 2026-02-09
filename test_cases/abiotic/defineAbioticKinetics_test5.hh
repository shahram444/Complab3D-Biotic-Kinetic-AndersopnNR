/* ============================================================================
 * defineAbioticKinetics_test5.hh - SEQUENTIAL DECAY CHAIN
 * ============================================================================
 * REACTIONS:  A -> B -> C
 * RATE LAWS:  dA/dt = -k1 * [A]
 *             dB/dt = +k1 * [A] - k2 * [B]
 *             dC/dt = +k2 * [B]
 *
 * VALIDATION:
 *   Mass balance: [A] + [B] + [C] = constant
 *   B shows transient peak (rises then falls)
 *   Final state: all converts to C
 * ============================================================================
 */
#ifndef DEFINE_ABIOTIC_KINETICS_HH
#define DEFINE_ABIOTIC_KINETICS_HH

#include <vector>

/* ============================================================================
 * USER PARAMETERS - Only define reaction rate constants here
 * ============================================================================
 */
namespace AbioticParams {
    constexpr double k1 = 2.0e-4;  // [1/s] A -> B
    constexpr double k2 = 1.0e-4;  // [1/s] B -> C
}

/* ============================================================================
 * KINETICS FUNCTION
 *
 * INPUT:  C     = vector of concentrations (from model)
 *                 C[0] = species A
 *                 C[1] = species B
 *                 C[2] = species C
 * OUTPUT: subsR = vector of RATES dC/dt (model multiplies by dt)
 * ============================================================================
 */
void defineAbioticRxnKinetics(
    std::vector<double> C,           // Concentrations [kg/m3]
    std::vector<double>& subsR,      // Output: rates dC/dt [kg/m3/s]
    plb::plint mask                  // Cell type (from geometry)
) {
    // Initialize rates to zero
    for (size_t i = 0; i < subsR.size(); ++i) {
        subsR[i] = 0.0;
    }

    // DECAY CHAIN: A -> B -> C
    if (C.size() >= 3) {
        double A = (C[0] > 0.0) ? C[0] : 0.0;
        double B = (C[1] > 0.0) ? C[1] : 0.0;

        double rate_A_to_B = AbioticParams::k1 * A;
        double rate_B_to_C = AbioticParams::k2 * B;

        subsR[0] = -rate_A_to_B;                  // A decays
        subsR[1] = +rate_A_to_B - rate_B_to_C;   // B: produced from A, decays to C
        subsR[2] = +rate_B_to_C;                  // C accumulates
    }
}

#endif // DEFINE_ABIOTIC_KINETICS_HH
