/* ============================================================================
 * defineKinetics.hh - Scenario 09: Coupled Biotic + Abiotic Reactions
 * CompLaB3D - University of Georgia
 *
 * Sessile biofilm (CA solver) consumes DOC via Monod kinetics and produces
 * a Byproduct. The Byproduct then undergoes abiotic first-order decay
 * (handled in defineAbioticKinetics.hh).
 *
 * SPECIES MAPPING:
 *   B[0] = Sessile heterotroph biomass [kg/m3]     (CA solver)
 *   C[0] = DOC (dissolved organic carbon) [mol/L]   (consumed)
 *   C[1] = Byproduct [mol/L]                        (produced biotically)
 *
 * KINETICS MODEL:
 *   mu           = mu_max * DOC / (Ks + DOC)           (Monod growth)
 *   dB/dt        = (mu - k_decay) * B                  (net biomass change)
 *   dDOC/dt      = -mu * B / Y                         (DOC consumption)
 *   dByproduct/dt = -dDOC/dt * 0.5                     (50% of consumed DOC
 *                                                        becomes Byproduct)
 *
 * NOTES:
 *   - subsR[0] = DOC rate (negative = consumed)
 *   - subsR[1] = Byproduct rate from biotic process (positive = produced)
 *   - The abiotic decay of Byproduct is handled separately in
 *     defineAbioticKinetics.hh; the solver sums both contributions.
 *
 * STABILITY:
 *   DOC consumption is clamped to MAX_FRAC of available DOC per timestep.
 * ============================================================================
 */
#ifndef DEFINE_KINETICS_HH
#define DEFINE_KINETICS_HH

#include <vector>
#include <cmath>
#include <algorithm>
#include <iostream>
#include <iomanip>

// ============================================================================
// KINETIC PARAMETERS
// ============================================================================
namespace KineticParams {
    constexpr double mu_max   = 0.05;      // [1/s] maximum specific growth rate
    constexpr double Ks       = 1.0e-5;    // [mol/L] half-saturation constant for DOC
    constexpr double Y        = 0.4;       // [-] yield coefficient (biomass / substrate)
    constexpr double k_decay  = 1.0e-7;    // [1/s] first-order biomass decay rate

    // Byproduct stoichiometry
    constexpr double BYPRODUCT_YIELD = 0.5; // 50% of consumed DOC becomes Byproduct

    // Numerical stability
    constexpr double MIN_CONC = 1.0e-20;   // [mol/L] minimum concentration threshold
    constexpr double MIN_BIOMASS = 0.1;    // [kg/m3] minimum biomass to consider active
    constexpr double MAX_FRAC = 0.5;       // max fraction of DOC consumed per timestep
    constexpr double dt_kinetics = 0.0075; // [s] kinetics timestep
}

// ============================================================================
// KINETICS STATISTICS ACCUMULATOR
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
        iter_sum_dB = 0.0; iter_sum_dDOC = 0.0; iter_max_biomass = 0.0;
        iter_max_dB = 0.0; iter_min_DOC = 1e30;
        iter_cells_with_biomass = 0; iter_cells_with_growth = 0;
        iter_total_calls = 0; iter_cells_limited = 0;
    }
    inline void accumulate(double biomass, double DOC, double dB_dt, double dDOC_dt, bool was_limited) {
        iter_total_calls++;
        if (biomass > 0.1) {
            iter_cells_with_biomass++;
            iter_sum_dB += dB_dt; iter_sum_dDOC += dDOC_dt;
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
    inline void getStats(long& cells_biomass, long& cells_growth, double& sum_dB,
                         double& max_B, double& max_dB, double& min_DOC) {
        cells_biomass = iter_cells_with_biomass; cells_growth = iter_cells_with_growth;
        sum_dB = iter_sum_dB; max_B = iter_max_biomass; max_dB = iter_max_dB;
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

    // Initialize all output rates to zero
    for (size_t i = 0; i < subsR.size(); ++i) subsR[i] = 0.0;
    for (size_t i = 0; i < bioR.size(); ++i) bioR[i] = 0.0;

    // Guard: need at least one biomass and two substrates
    if (B.empty() || C.empty()) return;

    // Extract biomass
    double biomass = std::max(B[0], 0.0);
    if (biomass < MIN_BIOMASS) return;

    // Extract DOC concentration
    double DOC_raw = C[0];
    double DOC = std::max(DOC_raw, MIN_CONC);

    // --- Monod kinetics ---
    double monod = DOC / (Ks + DOC);
    double mu = mu_max * monod;
    double net_mu = mu - k_decay;

    // Unclamped rates
    double dB_dt_unclamped = net_mu * biomass;
    double dDOC_dt_unclamped = -mu * biomass / Y;

    // --- Stability clamping ---
    double max_consumable_DOC = DOC * MAX_FRAC;
    double max_consumption_rate = max_consumable_DOC / dt_kinetics;

    bool substrate_limited = false;
    double dDOC_dt = dDOC_dt_unclamped;
    double dB_dt = dB_dt_unclamped;

    if (-dDOC_dt_unclamped > max_consumption_rate) {
        substrate_limited = true;
        dDOC_dt = -max_consumption_rate;
        // Recalculate growth based on actual substrate availability
        double actual_mu = max_consumption_rate * Y / biomass;
        double actual_net_mu = actual_mu - k_decay;
        dB_dt = actual_net_mu * biomass;
    }

    // Handle depleted substrate
    if (DOC_raw <= MIN_CONC) {
        dDOC_dt = 0.0;
        dB_dt = std::min(dB_dt, -k_decay * biomass);
    }

    // Byproduct production: 50% of consumed DOC becomes Byproduct
    // dDOC_dt is negative (consumption), so -dDOC_dt is positive
    double dByproduct_dt = -dDOC_dt * BYPRODUCT_YIELD;

    // Accumulate statistics
    KineticsStats::accumulate(biomass, DOC_raw, dB_dt, dDOC_dt, substrate_limited);

    // Set output rates
    if (subsR.size() > 0) subsR[0] = dDOC_dt;        // DOC consumption (negative)
    if (subsR.size() > 1) subsR[1] = dByproduct_dt;  // Byproduct production (positive)
    if (bioR.size() > 0)  bioR[0] = dB_dt;           // biomass change

    // Output validation
    if (std::isnan(dB_dt) || std::isnan(dDOC_dt) || std::isnan(dByproduct_dt)) {
        std::cerr << "[KINETICS ERROR] NaN detected! B=" << biomass
                  << " DOC=" << DOC_raw << "\n";
    }
}

#endif // DEFINE_KINETICS_HH
