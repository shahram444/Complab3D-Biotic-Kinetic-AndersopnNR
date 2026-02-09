/* ============================================================================
 * defineAbioticKinetics_test4.hh - REVERSIBLE REACTION
 * ============================================================================
 * REACTION:   A <-> B
 * RATE LAW:   dA/dt = -k_f*[A] + k_r*[B]
 *             dB/dt = +k_f*[A] - k_r*[B]
 *
 * EQUILIBRIUM:
 *   K_eq = k_f / k_r = 2.0
 *   At equilibrium: [B]/[A] = K_eq
 *
 * VALIDATION:
 *   Conservation: [A] + [B] = constant
 *   If [A]_0=1.0, [B]_0=0: equilibrium at [A]=0.333, [B]=0.667
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
    constexpr double k_forward = 1.0e-3;  // [1/s] A -> B
    constexpr double k_reverse = 5.0e-4;  // [1/s] B -> A
    // K_eq = k_f/k_r = 2.0
}

/* ============================================================================
 * KINETICS FUNCTION
 *
 * INPUT:  C     = vector of concentrations (from model)
 *                 C[0] = species A
 *                 C[1] = species B
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

    // REVERSIBLE: A <-> B
    if (C.size() >= 2) {
        double A = (C[0] > 0.0) ? C[0] : 0.0;
        double B = (C[1] > 0.0) ? C[1] : 0.0;

        // Net rate: forward - reverse
        double net_rate = AbioticParams::k_forward * A - AbioticParams::k_reverse * B;

        subsR[0] = -net_rate;  // A: decreases if forward > reverse
        subsR[1] = +net_rate;  // B: increases if forward > reverse
    }
}

#endif // DEFINE_ABIOTIC_KINETICS_HH
