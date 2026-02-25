/* ============================================================================
 * defineKinetics.hh - Scenario 08: Sessile Biofilm (CA) + Planktonic (LBM)
 * CompLaB3D - University of Georgia
 *
 * Two microbial populations competing for one substrate (DOC):
 *   - Sessile heterotroph: attached to walls, solved by Cellular Automaton
 *   - Planktonic heterotroph: free-floating, solved by LBM advection-diffusion
 * Both consume dissolved organic carbon (DOC) via Monod kinetics.
 *
 * SPECIES MAPPING:
 *   B[0] = Sessile heterotroph biomass [kg/m3]     (CA solver)
 *   B[1] = Planktonic heterotroph biomass [kg/m3]   (LBM solver)
 *   C[0] = DOC (dissolved organic carbon) [mol/L]
 *
 * KINETICS MODEL (per species i):
 *   mu_i     = mu_max_i * DOC / (Ks_i + DOC)
 *   dB_i/dt  = (mu_i - k_decay_i) * B_i
 *   dDOC/dt  = sum_i( -mu_i * B_i / Y_i )         (combined consumption)
 *
 * STABILITY:
 *   Combined DOC consumption is clamped to MAX_FRAC of available DOC per
 *   timestep. When clamped, each species' consumption is scaled
 *   proportionally to its unclamped demand.
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
    // --- Sessile heterotroph (B[0], CA solver) ---
    constexpr double mu_max_s   = 0.05;    // [1/s] max specific growth rate
    constexpr double Ks_s       = 1.0e-5;  // [mol/L] half-saturation constant
    constexpr double Y_s        = 0.4;     // [-] yield coefficient
    constexpr double k_decay_s  = 1.0e-7;  // [1/s] biomass decay rate

    // --- Planktonic heterotroph (B[1], LBM solver) ---
    constexpr double mu_max_p   = 0.03;    // [1/s] max specific growth rate
    constexpr double Ks_p       = 1.0e-5;  // [mol/L] half-saturation constant
    constexpr double Y_p        = 0.35;    // [-] yield coefficient
    constexpr double k_decay_p  = 1.0e-7;  // [1/s] biomass decay rate

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

    // Guard: need biomass and substrate vectors
    if (B.size() < 2 || C.empty()) return;

    // Extract DOC concentration
    double DOC_raw = C[0];
    double DOC = std::max(DOC_raw, MIN_CONC);

    // Extract biomass for each species
    double bio_s = std::max(B[0], 0.0);  // sessile
    double bio_p = std::max(B[1], 0.0);  // planktonic

    bool any_active = (bio_s >= MIN_BIOMASS) || (bio_p >= MIN_BIOMASS);
    if (!any_active) return;

    // --- Monod kinetics for each species ---
    double monod_s = DOC / (Ks_s + DOC);
    double mu_s = mu_max_s * monod_s;

    double monod_p = DOC / (Ks_p + DOC);
    double mu_p = mu_max_p * monod_p;

    // Unclamped rates -- sessile
    double dB_s = 0.0, dDOC_s = 0.0;
    if (bio_s >= MIN_BIOMASS) {
        dB_s   = (mu_s - k_decay_s) * bio_s;
        dDOC_s = -mu_s * bio_s / Y_s;
    }

    // Unclamped rates -- planktonic
    double dB_p = 0.0, dDOC_p = 0.0;
    if (bio_p >= MIN_BIOMASS) {
        dB_p   = (mu_p - k_decay_p) * bio_p;
        dDOC_p = -mu_p * bio_p / Y_p;
    }

    // Total unclamped DOC consumption (negative value)
    double dDOC_total_unclamped = dDOC_s + dDOC_p;

    // --- Stability clamping on combined consumption ---
    double max_consumable_DOC = DOC * MAX_FRAC;
    double max_consumption_rate = max_consumable_DOC / dt_kinetics;

    bool substrate_limited = false;
    double dDOC_total = dDOC_total_unclamped;

    if (-dDOC_total_unclamped > max_consumption_rate) {
        substrate_limited = true;
        // Scale each species proportionally
        double total_demand = -dDOC_total_unclamped;  // positive
        double scale = max_consumption_rate / total_demand;

        dDOC_s *= scale;
        dDOC_p *= scale;
        dDOC_total = -(max_consumption_rate);

        // Recalculate growth based on actual consumption
        if (bio_s >= MIN_BIOMASS) {
            double actual_mu_s = (-dDOC_s) * Y_s / bio_s;
            dB_s = (actual_mu_s - k_decay_s) * bio_s;
        }
        if (bio_p >= MIN_BIOMASS) {
            double actual_mu_p = (-dDOC_p) * Y_p / bio_p;
            dB_p = (actual_mu_p - k_decay_p) * bio_p;
        }
    }

    // Handle depleted substrate
    if (DOC_raw <= MIN_CONC) {
        dDOC_s = 0.0;
        dDOC_p = 0.0;
        dDOC_total = 0.0;
        if (bio_s >= MIN_BIOMASS) dB_s = std::min(dB_s, -k_decay_s * bio_s);
        if (bio_p >= MIN_BIOMASS) dB_p = std::min(dB_p, -k_decay_p * bio_p);
    }

    // Accumulate statistics (combined biomass for tracking)
    double total_biomass = bio_s + bio_p;
    double total_dB = dB_s + dB_p;
    KineticsStats::accumulate(total_biomass, DOC_raw, total_dB, dDOC_total, substrate_limited);

    // Set output rates
    if (subsR.size() > 0) subsR[0] = dDOC_s + dDOC_p;  // combined DOC consumption
    if (bioR.size() > 0)  bioR[0] = dB_s;               // sessile biomass change
    if (bioR.size() > 1)  bioR[1] = dB_p;               // planktonic biomass change

    // Output validation
    if (std::isnan(dB_s) || std::isnan(dB_p) || std::isnan(dDOC_total)) {
        std::cerr << "[KINETICS ERROR] NaN detected! B_s=" << bio_s
                  << " B_p=" << bio_p << " DOC=" << DOC_raw << "\n";
    }
}

#endif // DEFINE_KINETICS_HH
