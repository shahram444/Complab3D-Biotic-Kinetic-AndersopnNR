/* ==========================================================================
 * defineAbioticKinetics.hh  --  First-order decay: A -> products
 *
 * Scenario: 1 substrate decays at rate k
 *   dC[0]/dt = -k * C[0]
 *
 * XML setup:
 *   enable_abiotic_kinetics = true
 *   1 substrate (Reactant), Dirichlet left BC
 *
 * Recompile after copying to source root:
 *     cd build && cmake .. && make -j$(nproc)
 * ========================================================================== */
#ifndef DEFINE_ABIOTIC_KINETICS_HH
#define DEFINE_ABIOTIC_KINETICS_HH

#include <vector>
#include <cmath>
#include <iostream>

namespace AbioticParams {
    constexpr double k_decay   = 1.0e-5;   // [1/s] first-order rate
    constexpr double MIN_CONC  = 1.0e-20;
    constexpr double MAX_FRAC  = 0.5;       // stability clamp
    constexpr double dt        = 0.0075;    // [s] kinetics timestep
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

    if (C.size() < 1) return;

    double A = std::max(C[0], MIN_CONC);
    double rate = -k_decay * A;

    // Clamp: don't consume more than MAX_FRAC per timestep
    double max_rate = A * MAX_FRAC / dt;
    if (-rate > max_rate) rate = -max_rate;

    subsR[0] = rate;
    AbioticKineticsStats::accumulate(rate);
}

#endif
