/* ============================================================================
 * defineKinetics.hh - EXTREME GROWTH VERSION (BIOFILM)
 * CompLaB3D - University of Georgia
 *
 * CHANGES FOR EXTREME GROWTH:
 *   - mu_max increased from 0.05 to 1.0 (20x faster)
 *   - k_decay reduced to 1.0e-9 (less die-off)
 *   - DOC consumption clamping still active for stability
 *
 * VALIDATION FEATURES:
 *   - Input validation at startup
 *   - Per-iteration diagnostics showing kinetics working
 *   - Mass balance tracking for verification
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
        std::cout << "║           KINETICS PARAMETER VALIDATION (BIOFILM)                    ║\n";
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
}

// ============================================================================
// ITERATION DIAGNOSTICS - DETAILED PER-ITERATION OUTPUT
// ============================================================================
namespace KineticsDiagnostics {
    // Mass balance tracking
    static double total_biomass_produced = 0.0;
    static double total_DOC_consumed = 0.0;
    static long total_iterations = 0;
    static long total_kinetics_calls = 0;

    inline void resetAll() {
        total_biomass_produced = 0.0;
        total_DOC_consumed = 0.0;
        total_iterations = 0;
        total_kinetics_calls = 0;
    }

    inline void recordIteration(double dB, double dDOC) {
        total_biomass_produced += dB;
        total_DOC_consumed += (-dDOC);
        total_kinetics_calls++;
    }

    inline void incrementIteration() {
        total_iterations++;
    }

    /**
     * Print detailed iteration diagnostics
     */
    inline void printIterationSummary(long iteration) {
        using namespace KineticsStats;

        std::cout << std::fixed << std::setprecision(6);
        std::cout << "┌─────────────────────────────────────────────────────────────────┐\n";
        std::cout << "│ KINETICS ITERATION " << iteration << " DIAGNOSTICS (BIOFILM)              \n";
        std::cout << "├─────────────────────────────────────────────────────────────────┤\n";
        std::cout << "│ Kinetics calls this iter: " << iter_total_calls << "\n";

        if (iter_cells_with_biomass > 0) {
            std::cout << "│ BIOMASS:\n";
            std::cout << "│   Cells with biomass:  " << iter_cells_with_biomass << "\n";
            std::cout << "│   Cells growing:       " << iter_cells_with_growth << " ("
                      << std::fixed << std::setprecision(1)
                      << (100.0 * iter_cells_with_growth / iter_cells_with_biomass) << "%)\n";
            std::cout << "│   Substrate limited:   " << iter_cells_limited << "\n";
            std::cout << "│   Max biomass:         " << std::scientific << iter_max_biomass << " kg/m³\n";

            std::cout << "│ GROWTH RATES:\n";
            std::cout << "│   Sum dB/dt:           " << iter_sum_dB << " kg/m³/s\n";
            std::cout << "│   Max dB/dt:           " << iter_max_dB << " kg/m³/s\n";

            std::cout << "│ SUBSTRATE:\n";
            std::cout << "│   Sum dDOC/dt:         " << iter_sum_dDOC << " mol/L/s (negative=consumed)\n";
            std::cout << "│   Min DOC in biofilm:  " << iter_min_DOC << " mol/L\n";

            // Mass balance check
            std::cout << "│ MASS BALANCE CHECK:\n";
            double expected = iter_sum_dB / KineticParams::Y;
            double actual = -iter_sum_dDOC;
            double error = (expected > 0) ? std::abs(actual - expected) / expected * 100.0 : 0.0;
            std::cout << "│   Expected DOC use:    " << expected << " mol/L/s\n";
            std::cout << "│   Actual DOC use:      " << actual << " mol/L/s\n";
            std::cout << "│   Balance error:       " << std::fixed << std::setprecision(2) << error << "%";
            if (error < 5.0) std::cout << " ✓ OK\n";
            else std::cout << " ⚠ CHECK CLAMPING\n";
        } else {
            std::cout << "│ NO ACTIVE BIOMASS CELLS (B < MIN_BIOMASS)\n";
        }

        std::cout << "│ CUMULATIVE: iters=" << total_iterations << " calls=" << total_kinetics_calls << "\n";
        std::cout << "└─────────────────────────────────────────────────────────────────┘\n";
        std::cout << std::fixed;
    }

    /**
     * Print quick one-line status
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

    // Record for mass balance tracking
    KineticsDiagnostics::recordIteration(dB_dt, dDOC_dt);

    if (subsR.size() > 0) subsR[0] = dDOC_dt;
    if (subsR.size() > 1) subsR[1] = dCO2_dt;
    if (bioR.size() > 0) bioR[0] = dB_dt;

    // Output validation
    if (std::isnan(dB_dt) || std::isnan(dDOC_dt)) {
        std::cerr << "[KINETICS ERROR] NaN detected! B=" << biomass << " DOC=" << DOC_raw << "\n";
    }
    if (std::abs(dB_dt) > 1e6 || std::abs(dDOC_dt) > 1e6) {
        std::cerr << "[KINETICS WARNING] Large rates! dB=" << dB_dt << " dDOC=" << dDOC_dt << "\n";
    }
}

#endif // DEFINE_KINETICS_HH
