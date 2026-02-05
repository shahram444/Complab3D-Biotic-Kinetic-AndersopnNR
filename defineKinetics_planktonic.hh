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
 *
 * VALIDATION FEATURES:
 *   - Input validation at startup
 *   - Per-iteration diagnostics showing kinetics working
 *   - Mass balance tracking for verification
 * ============================================================================
 */
#ifndef DEFINE_KINETICS_PLANKTONIC_HH
#define DEFINE_KINETICS_PLANKTONIC_HH

#include <vector>
#include <cmath>
#include <algorithm>
#include <iostream>
#include <iomanip>

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
// INPUT VALIDATION - VERIFY PARAMETERS AT STARTUP
// ============================================================================
namespace KineticsValidation {

    /**
     * Validate kinetic parameters at startup
     * Call this once when simulation starts to verify all inputs are correct
     * Returns true if all parameters are valid
     */
    inline bool validateParameters() {
        using namespace KineticParams;
        bool all_ok = true;

        std::cout << "\n";
        std::cout << "╔══════════════════════════════════════════════════════════════════════╗\n";
        std::cout << "║           KINETICS PARAMETER VALIDATION (PLANKTONIC)                 ║\n";
        std::cout << "╠══════════════════════════════════════════════════════════════════════╣\n";

        // Check mu_max
        std::cout << "║ mu_max     = " << std::scientific << std::setprecision(2) << mu_max << " [1/s]   ";
        if (mu_max > 0 && mu_max < 10.0) {
            std::cout << "✓ OK (reasonable growth rate)\n";
        } else if (mu_max <= 0) {
            std::cout << "✗ FAIL: Must be positive!\n";
            all_ok = false;
        } else {
            std::cout << "⚠ WARN: Very high growth rate\n";
        }

        // Check Ks
        std::cout << "║ Ks         = " << std::scientific << Ks << " [mol/L] ";
        if (Ks > 0 && Ks < 1.0) {
            std::cout << "✓ OK (typical half-saturation)\n";
        } else if (Ks <= 0) {
            std::cout << "✗ FAIL: Must be positive!\n";
            all_ok = false;
        } else {
            std::cout << "⚠ WARN: Unusual value\n";
        }

        // Check yield coefficient
        std::cout << "║ Y          = " << std::fixed << std::setprecision(2) << Y << "       [-]     ";
        if (Y > 0 && Y <= 1.0) {
            std::cout << "✓ OK (0 < Y <= 1)\n";
        } else {
            std::cout << "✗ FAIL: Y must be in (0,1]!\n";
            all_ok = false;
        }

        // Check decay
        std::cout << "║ k_decay    = " << std::scientific << std::setprecision(2) << k_decay << " [1/s]   ";
        if (k_decay >= 0 && k_decay < mu_max) {
            std::cout << "✓ OK (decay < growth)\n";
        } else if (k_decay >= mu_max) {
            std::cout << "⚠ WARN: decay >= growth (net negative growth!)\n";
        } else {
            std::cout << "✗ FAIL: Negative decay!\n";
            all_ok = false;
        }

        // Check dt_kinetics
        std::cout << "║ dt_kinetics= " << std::scientific << dt_kinetics << " [s]     ";
        if (dt_kinetics > 0 && dt_kinetics < 1.0) {
            std::cout << "✓ OK\n";
        } else {
            std::cout << "✗ FAIL: Invalid timestep!\n";
            all_ok = false;
        }

        // Check MIN_BIOMASS
        std::cout << "║ MIN_BIOMASS= " << std::scientific << MIN_BIOMASS << " [kg/m³] ";
        if (MIN_BIOMASS > 0) {
            std::cout << "✓ OK\n";
        } else {
            std::cout << "✗ FAIL: Must be positive!\n";
            all_ok = false;
        }

        std::cout << "╠══════════════════════════════════════════════════════════════════════╣\n";
        if (all_ok) {
            std::cout << "║ VALIDATION RESULT: ✓ ALL PARAMETERS OK                               ║\n";
        } else {
            std::cout << "║ VALIDATION RESULT: ✗ ERRORS FOUND - CHECK PARAMETERS!               ║\n";
        }
        std::cout << "╚══════════════════════════════════════════════════════════════════════╝\n\n";

        return all_ok;
    }

    /**
     * Validate input vectors before kinetics calculation
     * Returns true if inputs are valid
     */
    inline bool validateInputs(const std::vector<double>& B,
                               const std::vector<double>& C,
                               std::vector<double>& subsR,
                               std::vector<double>& bioR) {
        bool valid = true;

        // Check vector sizes
        if (B.empty()) {
            std::cerr << "[KINETICS ERROR] Biomass vector is empty!\n";
            valid = false;
        }
        if (C.empty()) {
            std::cerr << "[KINETICS ERROR] Substrate vector is empty!\n";
            valid = false;
        }
        if (subsR.empty()) {
            std::cerr << "[KINETICS ERROR] Substrate rate vector is empty!\n";
            valid = false;
        }
        if (bioR.empty()) {
            std::cerr << "[KINETICS ERROR] Biomass rate vector is empty!\n";
            valid = false;
        }

        // Check for NaN in inputs
        if (!B.empty() && std::isnan(B[0])) {
            std::cerr << "[KINETICS ERROR] Biomass is NaN!\n";
            valid = false;
        }
        if (!C.empty() && std::isnan(C[0])) {
            std::cerr << "[KINETICS ERROR] DOC concentration is NaN!\n";
            valid = false;
        }

        return valid;
    }
}

// ============================================================================
// ITERATION DIAGNOSTICS - DETAILED PER-ITERATION OUTPUT
// ============================================================================
namespace KineticsDiagnostics {
    // Mass balance tracking
    static double total_biomass_produced = 0.0;
    static double total_DOC_consumed = 0.0;
    static double total_CO2_produced = 0.0;
    static long total_iterations = 0;
    static long total_kinetics_calls = 0;

    // Per-iteration tracking
    static double iter_biomass_start = 0.0;
    static double iter_biomass_end = 0.0;
    static double iter_DOC_start = 0.0;
    static double iter_DOC_end = 0.0;

    inline void resetAll() {
        total_biomass_produced = 0.0;
        total_DOC_consumed = 0.0;
        total_CO2_produced = 0.0;
        total_iterations = 0;
        total_kinetics_calls = 0;
    }

    inline void recordIteration(double dB, double dDOC, double dCO2) {
        total_biomass_produced += dB;
        total_DOC_consumed += (-dDOC);  // dDOC is negative for consumption
        total_CO2_produced += dCO2;
        total_kinetics_calls++;
    }

    inline void incrementIteration() {
        total_iterations++;
    }

    /**
     * Print detailed iteration diagnostics
     * Call this at end of each iteration or at intervals
     */
    inline void printIterationSummary(long iteration, double dt) {
        using namespace KineticsStats;

        std::cout << std::fixed << std::setprecision(6);
        std::cout << "┌─────────────────────────────────────────────────────────────────┐\n";
        std::cout << "│ KINETICS ITERATION " << iteration << " DIAGNOSTICS                         \n";
        std::cout << "├─────────────────────────────────────────────────────────────────┤\n";

        // Show if kinetics was actually called
        std::cout << "│ Kinetics calls this iter: " << iter_total_calls << "\n";

        if (iter_cells_with_biomass > 0) {
            std::cout << "│ BIOMASS:\n";
            std::cout << "│   Cells with biomass:  " << iter_cells_with_biomass << "\n";
            std::cout << "│   Cells growing:       " << iter_cells_with_growth << " ("
                      << std::fixed << std::setprecision(1)
                      << (100.0 * iter_cells_with_growth / iter_cells_with_biomass) << "%)\n";
            std::cout << "│   Cells decaying:      " << iter_cells_decaying << "\n";
            std::cout << "│   Substrate limited:   " << iter_cells_limited << "\n";
            std::cout << "│   Max biomass:         " << std::scientific << iter_max_biomass << " kg/m³\n";
            std::cout << "│   Avg biomass:         " << getAvgBiomass() << " kg/m³\n";

            std::cout << "│ GROWTH RATES:\n";
            std::cout << "│   Sum dB/dt:           " << iter_sum_dB << " kg/m³/s\n";
            std::cout << "│   Max dB/dt:           " << iter_max_dB << " kg/m³/s\n";

            std::cout << "│ SUBSTRATE:\n";
            std::cout << "│   Sum dDOC/dt:         " << iter_sum_dDOC << " mol/L/s (negative=consumed)\n";
            std::cout << "│   Min DOC in cells:    " << iter_min_DOC << " mol/L\n";

            // Mass balance check
            std::cout << "│ MASS BALANCE CHECK:\n";
            double expected_DOC_consumption = iter_sum_dB / KineticParams::Y;
            double actual_DOC_consumption = -iter_sum_dDOC;
            double balance_error = (expected_DOC_consumption > 0) ?
                std::abs(actual_DOC_consumption - expected_DOC_consumption) / expected_DOC_consumption * 100.0 : 0.0;
            std::cout << "│   Expected DOC use:    " << expected_DOC_consumption << " mol/L/s\n";
            std::cout << "│   Actual DOC use:      " << actual_DOC_consumption << " mol/L/s\n";
            std::cout << "│   Balance error:       " << std::fixed << std::setprecision(2) << balance_error << "%";
            if (balance_error < 5.0) {
                std::cout << " ✓ OK\n";
            } else {
                std::cout << " ⚠ CHECK CLAMPING\n";
            }

            std::cout << std::fixed << std::setprecision(6);
        } else {
            std::cout << "│ NO ACTIVE BIOMASS CELLS (B < MIN_BIOMASS)\n";
            std::cout << "│ This is normal if:\n";
            std::cout << "│   - Simulation just started\n";
            std::cout << "│   - Planktonic cells haven't reached pore space yet\n";
            std::cout << "│   - All cells have decayed\n";
        }

        std::cout << "│ CUMULATIVE TOTALS:\n";
        std::cout << "│   Total iterations:    " << total_iterations << "\n";
        std::cout << "│   Total kinetics calls:" << total_kinetics_calls << "\n";
        std::cout << "│   Total biomass prod:  " << std::scientific << total_biomass_produced << " kg/m³\n";
        std::cout << "│   Total DOC consumed:  " << total_DOC_consumed << " mol/L\n";
        std::cout << "└─────────────────────────────────────────────────────────────────┘\n";
        std::cout << std::fixed;
    }

    /**
     * Print quick one-line status (for every iteration)
     */
    inline void printQuickStatus(long iteration) {
        using namespace KineticsStats;

        std::cout << "[KIN " << iteration << "] ";
        std::cout << "cells=" << iter_cells_with_biomass;
        std::cout << " growing=" << iter_cells_with_growth;
        std::cout << " sumDOC=" << std::scientific << std::setprecision(2) << iter_sum_dDOC;
        std::cout << " sumB=" << iter_sum_dB;
        std::cout << std::fixed << "\n";
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

    // Record for mass balance tracking
    KineticsDiagnostics::recordIteration(dB_dt, dDOC_dt, dCO2_dt);

    // ========================================
    // SET OUTPUT REACTION RATES
    // ========================================
    // Substrate rates
    if (subsR.size() > 0) subsR[0] = dDOC_dt;    // DOC consumption (negative)
    if (subsR.size() > 1) subsR[1] = dCO2_dt;    // CO2 production (positive)
    // HCO3, CO3, H+ unchanged (no equilibrium solver)

    // Biomass rates
    if (bioR.size() > 0) bioR[0] = dB_dt;        // planktonic biomass change

    // ========================================
    // OUTPUT VALIDATION (detect errors)
    // ========================================
    // Check for NaN in outputs
    if (std::isnan(dB_dt) || std::isnan(dDOC_dt) || std::isnan(dCO2_dt)) {
        std::cerr << "[KINETICS ERROR] NaN detected in output!\n";
        std::cerr << "  Inputs: B=" << biomass << " DOC=" << DOC_raw << "\n";
        std::cerr << "  Outputs: dB=" << dB_dt << " dDOC=" << dDOC_dt << " dCO2=" << dCO2_dt << "\n";
    }

    // Check for unreasonably large rates
    if (std::abs(dB_dt) > 1e6 || std::abs(dDOC_dt) > 1e6) {
        std::cerr << "[KINETICS WARNING] Very large rates detected!\n";
        std::cerr << "  dB/dt=" << dB_dt << " dDOC/dt=" << dDOC_dt << "\n";
    }
}

#endif // DEFINE_KINETICS_PLANKTONIC_HH
