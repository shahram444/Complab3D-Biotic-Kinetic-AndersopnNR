/* ============================================================================
 * defineKinetics_planktonic.hh - PLANKTONIC BACTERIA VERSION
 * CompLaB3D - University of Georgia
 *
 * PLANKTONIC MODE CHARACTERISTICS:
 *   - Free-floating bacteria transported by advection-diffusion
 *   - Lower maximum growth rate than sessile biofilm cells
 *   - Higher decay rate (less environmental protection)
 *   - No biofilm-specific diffusion limitations
 *   - Biomass distributed throughout pore space
 * ============================================================================
 */
#ifndef DEFINE_KINETICS_PLANKTONIC_HH
#define DEFINE_KINETICS_PLANKTONIC_HH

#include <vector>
#include <cmath>
#include <algorithm>

// ============================================================================
// KINETIC PARAMETERS - PLANKTONIC BACTERIA SETTINGS
// ============================================================================
namespace KineticParams {
    // *** PLANKTONIC GROWTH PARAMETERS ***
    // Planktonic cells typically have moderate growth rates
    // compared to protected biofilm cells
    constexpr double mu_max   = 0.5;       // [1/s] maximum specific growth rate
    constexpr double Ks       = 1.0e-5;    // [mol/L] half saturation constant for DOC
    constexpr double Y        = 0.4;       // [-] yield coefficient (biomass/substrate)
    constexpr double k_decay  = 1.0e-7;    // [1/s] decay rate (higher than biofilm)

    // Numerical stability parameters
    constexpr double MIN_CONC = 1.0e-20;   // [mol/L] minimum concentration threshold
    constexpr double MIN_BIOMASS = 0.01;   // [kg/m3] minimum biomass to consider active
    constexpr double MAX_DOC_CONSUMPTION_FRACTION = 0.5;  // max fraction consumed per dt
    constexpr double dt_kinetics = 0.0075; // [s] kinetics timestep

    // Planktonic-specific parameters
    constexpr double PLANKTONIC_DILUTION_FACTOR = 1.0;  // account for dilution in flow
}

// ============================================================================
// DEBUG STATISTICS ACCUMULATOR - PLANKTONIC VERSION
// ============================================================================
namespace KineticsStats {
    // Per-iteration accumulators
    static double iter_sum_dB = 0.0;          // total biomass change rate
    static double iter_sum_dDOC = 0.0;        // total DOC change rate
    static double iter_max_biomass = 0.0;     // maximum biomass encountered
    static double iter_max_dB = 0.0;          // maximum growth rate
    static double iter_min_DOC = 1e30;        // minimum DOC concentration
    static double iter_avg_biomass = 0.0;     // average biomass (planktonic)
    static long iter_cells_with_biomass = 0;  // cells containing biomass
    static long iter_cells_with_growth = 0;   // cells with positive growth
    static long iter_total_calls = 0;         // total kinetics calls
    static long iter_cells_limited = 0;       // substrate-limited cells
    static long iter_cells_decaying = 0;      // cells with net decay

    inline void resetIteration() {
        iter_sum_dB = 0.0;
        iter_sum_dDOC = 0.0;
        iter_max_biomass = 0.0;
        iter_max_dB = 0.0;
        iter_min_DOC = 1e30;
        iter_avg_biomass = 0.0;
        iter_cells_with_biomass = 0;
        iter_cells_with_growth = 0;
        iter_total_calls = 0;
        iter_cells_limited = 0;
        iter_cells_decaying = 0;
    }

    inline void accumulate(double biomass, double DOC, double dB_dt, double dDOC_dt, bool was_limited) {
        iter_total_calls++;
        if (biomass > KineticParams::MIN_BIOMASS) {
            iter_cells_with_biomass++;
            iter_sum_dB += dB_dt;
            iter_sum_dDOC += dDOC_dt;
            iter_avg_biomass += biomass;

            if (biomass > iter_max_biomass) iter_max_biomass = biomass;
            if (dB_dt > iter_max_dB) iter_max_dB = dB_dt;
            if (DOC < iter_min_DOC && DOC > 0) iter_min_DOC = DOC;

            if (dB_dt > 0) iter_cells_with_growth++;
            if (dB_dt < 0) iter_cells_decaying++;
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
    inline long getDecayingCells() { return iter_cells_decaying; }
    inline double getAvgBiomass() {
        return (iter_cells_with_biomass > 0) ? iter_avg_biomass / iter_cells_with_biomass : 0.0;
    }
}

// ============================================================================
// MAIN KINETICS FUNCTION - PLANKTONIC VERSION
// ============================================================================
/**
 * Compute reaction kinetics for planktonic bacteria
 *
 * Model: Monod kinetics with decay
 *   mu = mu_max * S / (Ks + S)           - specific growth rate
 *   dB/dt = (mu - k_decay) * B           - net biomass change
 *   dS/dt = -mu * B / Y                  - substrate consumption
 *
 * @param B     Vector of biomass concentrations [kg/m3]
 *              B[0] = planktonic biomass (used in this version)
 * @param C     Vector of substrate concentrations [mol/L]
 *              C[0] = DOC (electron donor)
 *              C[1] = CO2 (product)
 * @param subsR Output: substrate reaction rates [mol/L/s]
 * @param bioR  Output: biomass reaction rates [kg/m3/s]
 * @param mask  Lattice mask value (geometry indicator)
 */
void defineRxnKinetics(
    std::vector<double> B,
    std::vector<double> C,
    std::vector<double>& subsR,
    std::vector<double>& bioR,
    plb::plint mask
) {
    using namespace KineticParams;

    // Initialize output rates to zero
    for (size_t i = 0; i < subsR.size(); ++i) subsR[i] = 0.0;
    for (size_t i = 0; i < bioR.size(); ++i) bioR[i] = 0.0;

    // Check for valid inputs
    if (B.empty() || C.empty()) return;

    // Get planktonic biomass (could be in B[0] for single-species planktonic)
    double biomass = std::max(B[0], 0.0);

    // Skip if biomass is below threshold
    if (biomass < MIN_BIOMASS) return;

    // Get substrate concentrations
    double DOC_raw = C[0];
    double DOC = std::max(DOC_raw, MIN_CONC);

    // ========================================
    // MONOD KINETICS FOR PLANKTONIC BACTERIA
    // ========================================

    // Monod growth function
    double monod = DOC / (Ks + DOC);

    // Specific growth rate
    double mu = mu_max * monod;

    // Net specific growth rate (growth - decay)
    double net_mu = mu - k_decay;

    // Unclamped rates
    double dB_dt_unclamped = net_mu * biomass;
    double dDOC_dt_unclamped = -mu * biomass / Y;

    // ========================================
    // SUBSTRATE LIMITATION CLAMPING
    // ========================================
    // Prevent consuming more DOC than available
    double max_consumable_DOC = DOC * MAX_DOC_CONSUMPTION_FRACTION;
    double max_consumption_rate = max_consumable_DOC / dt_kinetics;

    bool substrate_limited = false;
    double dDOC_dt = dDOC_dt_unclamped;
    double dB_dt = dB_dt_unclamped;
    double dCO2_dt;

    if (-dDOC_dt_unclamped > max_consumption_rate) {
        // Substrate-limited: clamp consumption
        substrate_limited = true;
        dDOC_dt = -max_consumption_rate;

        // Recalculate growth based on actual consumption
        double actual_mu = max_consumption_rate * Y / biomass;
        double actual_net_mu = actual_mu - k_decay;
        dB_dt = actual_net_mu * biomass;
        dCO2_dt = max_consumption_rate;  // CO2 produced = DOC consumed
    } else {
        dCO2_dt = -dDOC_dt;  // Stoichiometric CO2 production
    }

    // Handle depleted substrate case
    if (DOC_raw <= MIN_CONC) {
        dDOC_dt = 0.0;
        dCO2_dt = 0.0;
        // Only decay when no substrate
        dB_dt = std::min(dB_dt, -k_decay * biomass);
    }

    // ========================================
    // ACCUMULATE STATISTICS FOR DIAGNOSTICS
    // ========================================
    KineticsStats::accumulate(biomass, DOC_raw, dB_dt, dDOC_dt, substrate_limited);

    // ========================================
    // SET OUTPUT REACTION RATES
    // ========================================
    // Substrate rates
    if (subsR.size() > 0) subsR[0] = dDOC_dt;    // DOC consumption (negative)
    if (subsR.size() > 1) subsR[1] = dCO2_dt;    // CO2 production (positive)
    // HCO3, CO3, H+ unchanged (no equilibrium solver)

    // Biomass rates
    if (bioR.size() > 0) bioR[0] = dB_dt;        // planktonic biomass change
}

#endif // DEFINE_KINETICS_PLANKTONIC_HH
