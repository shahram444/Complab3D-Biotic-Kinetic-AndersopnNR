/* ============================================================================
 * defineAbioticKinetics_test3.hh - BIMOLECULAR REACTION
 * ============================================================================
 * REACTION:   A + B -> C
 * RATE LAW:   rate = k * [A] * [B]
 *             dA/dt = dB/dt = -rate
 *             dC/dt = +rate
 *
 * VALIDATION:
 *   Mass balance: [A] + [C] = [A]_0  (constant)
 *   Mass balance: [B] + [C] = [B]_0  (constant)
 *   Final: B exhausted first (limiting reagent)
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
    constexpr double k_bimol = 0.01;    // [m3/kg/s] second-order rate constant
}

/* ============================================================================
 * KINETICS FUNCTION
 *
 * INPUT:  C     = vector of concentrations (from model)
 *                 C[0] = species A
 *                 C[1] = species B
 *                 C[2] = species C (product)
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

    // BIMOLECULAR: A + B -> C
    // Rate: r = k * [A] * [B]
    if (C.size() >= 3 && C[0] > 0.0 && C[1] > 0.0) {
        double rate = AbioticParams::k_bimol * C[0] * C[1];

        subsR[0] = -rate;  // A consumed
        subsR[1] = -rate;  // B consumed
        subsR[2] = +rate;  // C produced
    }
}

#endif // DEFINE_ABIOTIC_KINETICS_HH
