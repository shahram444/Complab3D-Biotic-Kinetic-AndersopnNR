/* ============================================================================
 * defineAbioticKinetics_test2.hh - FIRST-ORDER DECAY
 * ============================================================================
 * REACTION:   A -> products
 * RATE LAW:   dA/dt = -k * [A]
 *
 * VALIDATION:
 *   Analytical solution: [A](t) = [A]_0 * exp(-k*t)
 *   Half-life: t_1/2 = ln(2)/k = 6931 seconds
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
    constexpr double k_decay = 1.0e-4;    // [1/s] decay rate constant
}

/* ============================================================================
 * KINETICS FUNCTION
 *
 * INPUT:  C     = vector of concentrations (from model)
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

    // FIRST-ORDER DECAY: A -> products
    // Rate: dA/dt = -k * [A]
    if (C.size() >= 1 && C[0] > 0.0) {
        subsR[0] = -AbioticParams::k_decay * C[0];
    }
}

#endif // DEFINE_ABIOTIC_KINETICS_HH
