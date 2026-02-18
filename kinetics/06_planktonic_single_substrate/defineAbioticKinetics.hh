/* ==========================================================================
 * defineAbioticKinetics.hh  --  No-op stub (flow-only simulation)
 *
 * Use with: flow_only template (no substrates, no microbes)
 *
 * Recompile after copying to source root:
 *     cd build && cmake .. && make -j$(nproc)
 * ========================================================================== */
#ifndef DEFINE_ABIOTIC_KINETICS_HH
#define DEFINE_ABIOTIC_KINETICS_HH

#include <vector>
#include <cmath>
#include <iostream>

namespace AbioticKineticsStats {
    static long iter_total_calls = 0;
    inline void resetIteration() { iter_total_calls = 0; }
    inline void accumulate(double) {}
}

void defineAbioticRxnKinetics(
    std::vector<double> C,
    std::vector<double>& subsR,
    plb::plint mask)
{
    for (auto& r : subsR) r = 0.0;
}

#endif
