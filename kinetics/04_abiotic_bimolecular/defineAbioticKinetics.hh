/* ==========================================================================
 * defineAbioticKinetics.hh  --  Bimolecular: A + B -> C
 *
 * Scenario: 3 substrates, second-order reaction
 *   dC[0]/dt = -k * C[0] * C[1]   (A consumed)
 *   dC[1]/dt = -k * C[0] * C[1]   (B consumed)
 *   dC[2]/dt = +k * C[0] * C[1]   (C produced)
 *
 * XML setup:
 *   enable_abiotic_kinetics = true
 *   3 substrates: A (Dirichlet), B (Dirichlet), C (Neumann)
 *
 * Recompile after copying to source root:
 *     cd build && cmake .. && make -j$(nproc)
 * ========================================================================== */
#ifndef DEFINE_ABIOTIC_KINETICS_HH
#define DEFINE_ABIOTIC_KINETICS_HH

#include <vector>
#include <cmath>
#include <algorithm>
#include <iostream>

namespace AbioticParams {
    constexpr double k_rxn    = 1.0e-3;    // [L/mol/s]
    constexpr double MIN_CONC = 1.0e-20;
    constexpr double MAX_FRAC = 0.5;
    constexpr double dt       = 0.0075;
}

namespace AbioticKineticsStats {
    static double iter_total_reaction = 0.0;
    static long iter_cells_reacting = 0;
    static long iter_total_calls = 0;
    inline void resetIteration() {
        iter_total_reaction = 0.0;
        iter_cells_reacting = 0;
        iter_total_calls = 0;
    }
    inline void accumulate(double r) {
        iter_total_calls++;
        if (std::abs(r) > 1e-20) {
            iter_cells_reacting++;
            iter_total_reaction += r;
        }
    }
}

void defineAbioticRxnKinetics(
    std::vector<double> C,
    std::vector<double>& subsR,
    plb::plint mask)
{
    using namespace AbioticParams;
    for (size_t i = 0; i < subsR.size(); ++i) subsR[i] = 0.0;

    if (C.size() < 3) return;

    double A = std::max(C[0], MIN_CONC);
    double B = std::max(C[1], MIN_CONC);
    double rate = k_rxn * A * B;

    // Clamp to prevent negative concentrations
    double max_A = A * MAX_FRAC / dt;
    double max_B = B * MAX_FRAC / dt;
    rate = std::min({rate, max_A, max_B});

    subsR[0] = -rate;   // A consumed
    subsR[1] = -rate;   // B consumed
    subsR[2] = +rate;   // C produced

    AbioticKineticsStats::accumulate(rate);
}

#endif
