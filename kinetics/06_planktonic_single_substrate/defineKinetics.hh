/* ==========================================================================
 * defineKinetics.hh  --  Monod biofilm kinetics (1 substrate, 1 microbe)
 *
 * Scenario: Sessile biofilm (CA solver) consumes DOC via Monod kinetics
 *   mu = mu_max * C[0] / (Ks + C[0])
 *   dB[0]/dt = (mu - k_decay) * B[0]
 *   dC[0]/dt = -mu * B[0] / Y
 *
 * XML setup:
 *   biotic_mode = true, enable_kinetics = true
 *   1 substrate (DOC), 1 microbe (CA solver)
 *
 * Recompile after copying to source root:
 *     cd build && cmake .. && make -j$(nproc)
 * ========================================================================== */
#ifndef DEFINE_KINETICS_HH
#define DEFINE_KINETICS_HH

#include <vector>
#include <cmath>
#include <algorithm>
#include <iostream>
#include <iomanip>

namespace KineticParams {
    constexpr double mu_max  = 0.05;    // [1/s] max growth rate
    constexpr double Ks      = 1.0e-5;  // [mol/L] half-saturation
    constexpr double Y       = 0.4;     // [-] yield
    constexpr double k_decay = 1.0e-7;  // [1/s] decay
    constexpr double MIN_CONC = 1.0e-20;
    constexpr double MIN_BIO  = 0.1;    // [kg/m3] below this = no growth
    constexpr double MAX_FRAC = 0.5;
    constexpr double dt       = 0.0075;
}

// Required by C++ solver (complab.cpp calls getStats / resetIteration)
namespace KineticsStats {
    static double iter_sum_dB = 0.0, iter_sum_dDOC = 0.0;
    static double iter_max_biomass = 0.0, iter_max_dB = 0.0;
    static double iter_min_DOC = 1e30;
    static long iter_cells_with_biomass = 0, iter_cells_with_growth = 0;
    static long iter_total_calls = 0, iter_cells_limited = 0;

    inline void resetIteration() {
        iter_sum_dB = iter_sum_dDOC = iter_max_biomass = iter_max_dB = 0.0;
        iter_min_DOC = 1e30;
        iter_cells_with_biomass = iter_cells_with_growth = 0;
        iter_total_calls = iter_cells_limited = 0;
    }
    inline void accumulate(double biomass, double DOC,
                           double dB, double dDOC, bool limited) {
        iter_total_calls++;
        if (biomass > KineticParams::MIN_BIO) {
            iter_cells_with_biomass++;
            iter_sum_dB += dB;
            iter_sum_dDOC += dDOC;
            if (biomass > iter_max_biomass) iter_max_biomass = biomass;
            if (dB > iter_max_dB) iter_max_dB = dB;
            if (DOC < iter_min_DOC && DOC > 0) iter_min_DOC = DOC;
            if (dB > 0) iter_cells_with_growth++;
            if (limited) iter_cells_limited++;
        }
    }
    inline void accumulate(double b, double d, double db, double dd) {
        accumulate(b, d, db, dd, false);
    }
    inline void getStats(long& cb, long& cg, double& sb, double& mb,
                         double& md, double& mi) {
        cb = iter_cells_with_biomass;
        cg = iter_cells_with_growth;
        sb = iter_sum_dB;
        mb = iter_max_biomass;
        md = iter_max_dB;
        mi = (iter_min_DOC < 1e20) ? iter_min_DOC : 0.0;
    }
    inline long getLimitedCells() { return iter_cells_limited; }
}

void defineRxnKinetics(
    std::vector<double> B,
    std::vector<double> C,
    std::vector<double>& subsR,
    std::vector<double>& bioR,
    plb::plint mask)
{
    using namespace KineticParams;
    for (auto& r : subsR) r = 0.0;
    for (auto& r : bioR)  r = 0.0;

    if (B.empty() || C.empty()) return;

    double biomass = std::max(B[0], 0.0);
    if (biomass < MIN_BIO) return;

    double DOC = std::max(C[0], MIN_CONC);

    // Monod kinetics
    double mu = mu_max * DOC / (Ks + DOC);
    double dB  = (mu - k_decay) * biomass;
    double dDOC = -mu * biomass / Y;

    // Clamp substrate consumption
    bool limited = false;
    double max_rate = DOC * MAX_FRAC / dt;
    if (-dDOC > max_rate) {
        limited = true;
        dDOC = -max_rate;
        dB = (max_rate * Y / biomass - k_decay) * biomass;
    }

    subsR[0] = dDOC;
    bioR[0]  = dB;

    KineticsStats::accumulate(biomass, C[0], dB, dDOC, limited);
}

#endif
