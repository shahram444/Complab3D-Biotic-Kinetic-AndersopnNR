/* ============================================================================
 * defineKinetics.hh - EXTREME GROWTH VERSION
 * CompLaB3D - University of Georgia
 *
 * Ported from old working settings to new CompLaB3D code.
 *
 * CHANGES FOR EXTREME GROWTH:
 *   - mu_max = 1.0 (20x faster than default 0.05)
 *   - k_decay = 1.0e-9 (minimal die-off)
 *   - DOC consumption clamping for stability
 *
 * SUBSTRATE MAPPING (must match CompLaB.xml):
 *   C[0] = DOC          (consumed by microbes)
 *   C[1] = CO2          (product of respiration)
 *   C[2] = HCO3         (not used in kinetics)
 *   C[3] = CO3          (not used in kinetics)
 *   C[4] = H+           (not used in kinetics)
 *
 * BIOMASS:
 *   B[0] = Heterotroph
 * ============================================================================
 */
#ifndef DEFINE_KINETICS_HH
#define DEFINE_KINETICS_HH

#include <vector>
#include <cmath>
#include <algorithm>

// ============================================================================
// KINETIC PARAMETERS - EXTREME GROWTH SETTINGS
// ============================================================================
namespace KineticParams {
    // *** EXTREME GROWTH PARAMETERS ***
    constexpr double mu_max   = 1.0;       // [1/s] *** 20x FASTER GROWTH! ***
    constexpr double Ks       = 1.0e-5;    // [mol/L] half saturation constant
    constexpr double Y        = 0.4;       // [-] yield coefficient
    constexpr double k_decay  = 1.0e-9;    // [1/s] *** REDUCED DECAY ***

    // Numerical stability
    constexpr double MIN_CONC = 1.0e-20;
    constexpr double MIN_BIOMASS = 0.1;
    constexpr double MAX_DOC_CONSUMPTION_FRACTION = 0.5;
    constexpr double dt_kinetics = 0.0075;
}

// ============================================================================
// DEBUG STATISTICS ACCUMULATOR
// ============================================================================
namespace KineticsStats {
    static double iter_sum_dB = 0.0;
    static double iter_sum_dDOC = 0.0;
    static double iter_max_biomass = 0.0;
    static double iter_max_dB = 0.0;
    static double iter_min_DOC = 1e30;
    static long iter_cells_with_biomass = 0;
    static long iter_cells_with_growth = 0;
    static long iter_total_calls = 0;
    static long iter_cells_limited = 0;

    inline void resetIteration() {
        iter_sum_dB = 0.0;
        iter_sum_dDOC = 0.0;
        iter_max_biomass = 0.0;
        iter_max_dB = 0.0;
        iter_min_DOC = 1e30;
        iter_cells_with_biomass = 0;
        iter_cells_with_growth = 0;
        iter_total_calls = 0;
        iter_cells_limited = 0;
    }

    inline void accumulate(double biomass, double DOC, double dB_dt, double dDOC_dt, bool was_limited) {
        iter_total_calls++;
        if (biomass > KineticParams::MIN_BIOMASS) {
            iter_cells_with_biomass++;
            iter_sum_dB += dB_dt;
            iter_sum_dDOC += dDOC_dt;
            if (biomass > iter_max_biomass) iter_max_biomass = biomass;
            if (dB_dt > iter_max_dB) iter_max_dB = dB_dt;
            if (DOC < iter_min_DOC && DOC > 0) iter_min_DOC = DOC;
            if (dB_dt > 0) iter_cells_with_growth++;
            if (was_limited) iter_cells_limited++;
        }
    }

    inline void accumulate(double biomass, double DOC, double dB_dt, double dDOC_dt) {
        accumulate(biomass, DOC, dB_dt, dDOC_dt, false);
    }

    inline void getStats(long& cells_biomass, long& cells_growth,
                         double& sum_dB, double& max_B, double& max_dB, double& min_DOC) {
        cells_biomass = iter_cells_with_biomass;
        cells_growth = iter_cells_with_growth;
        sum_dB = iter_sum_dB;
        max_B = iter_max_biomass;
        max_dB = iter_max_dB;
        min_DOC = (iter_min_DOC < 1e20) ? iter_min_DOC : 0.0;
    }

    inline long getLimitedCells() { return iter_cells_limited; }
}

// ============================================================================
// MAIN KINETICS FUNCTION
// ============================================================================
void defineRxnKinetics(
    std::vector<double> B,
    std::vector<double> C,
    std::vector<double>& subsR,
    std::vector<double>& bioR,
    plb::plint mask
) {
    using namespace KineticParams;

    for (size_t i = 0; i < subsR.size(); ++i) subsR[i] = 0.0;
    for (size_t i = 0; i < bioR.size(); ++i) bioR[i] = 0.0;

    if (B.empty() || C.empty()) return;

    double biomass = std::max(B[0], 0.0);
    if (biomass < MIN_BIOMASS) return;

    double DOC_raw = C[0];
    double DOC = std::max(DOC_raw, MIN_CONC);

    // Monod kinetics
    double monod = DOC / (Ks + DOC);
    double mu = mu_max * monod;
    double net_mu = mu - k_decay;

    double dB_dt_unclamped = net_mu * biomass;
    double dDOC_dt_unclamped = -mu * biomass / Y;

    // Clamp DOC consumption
    double max_consumable_DOC = DOC * MAX_DOC_CONSUMPTION_FRACTION;
    double max_consumption_rate = max_consumable_DOC / dt_kinetics;

    bool substrate_limited = false;
    double dDOC_dt = dDOC_dt_unclamped;
    double dB_dt = dB_dt_unclamped;
    double dCO2_dt;

    if (-dDOC_dt_unclamped > max_consumption_rate) {
        substrate_limited = true;
        dDOC_dt = -max_consumption_rate;
        double actual_mu = max_consumption_rate * Y / biomass;
        double actual_net_mu = actual_mu - k_decay;
        dB_dt = actual_net_mu * biomass;
        dCO2_dt = max_consumption_rate;
    } else {
        dCO2_dt = -dDOC_dt;
    }

    if (DOC_raw <= MIN_CONC) {
        dDOC_dt = 0.0;
        dCO2_dt = 0.0;
        dB_dt = std::min(dB_dt, -k_decay * biomass);
    }

    KineticsStats::accumulate(biomass, DOC_raw, dB_dt, dDOC_dt, substrate_limited);

    // Apply rates to substrate and biomass vectors
    if (subsR.size() > 0) subsR[0] = dDOC_dt;   // DOC consumed
    if (subsR.size() > 1) subsR[1] = dCO2_dt;   // CO2 produced
    if (bioR.size() > 0) bioR[0] = dB_dt;        // Biomass growth
}

#endif // DEFINE_KINETICS_HH
