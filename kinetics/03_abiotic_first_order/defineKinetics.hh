/* ==========================================================================
 * defineKinetics.hh  --  No-op stub (flow-only simulation)
 *
 * Use with: flow_only template (no substrates, no microbes)
 * The solver runs Navier-Stokes only.  Both .hh files must exist
 * because the solver #includes them unconditionally.
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
    constexpr double MIN_BIO = 0.1;
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
    inline void accumulate(double, double, double, double, bool) {}
    inline void accumulate(double, double, double, double) {}
    inline void getStats(long& cb, long& cg, double& sb, double& mb,
                         double& md, double& mi) {
        cb = cg = 0; sb = mb = md = mi = 0.0;
    }
    inline long getLimitedCells() { return 0; }
}

void defineRxnKinetics(
    std::vector<double> B,
    std::vector<double> C,
    std::vector<double>& subsR,
    std::vector<double>& bioR,
    plb::plint mask)
{
    for (auto& r : subsR) r = 0.0;
    for (auto& r : bioR)  r = 0.0;
}

#endif
