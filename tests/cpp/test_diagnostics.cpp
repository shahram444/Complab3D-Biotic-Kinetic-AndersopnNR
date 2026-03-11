// Unit tests for diagnostics, mass balance tracking, and statistics accumulators
// across both biotic (biofilm) and abiotic kinetics systems.

#include "plb_shim.h"
#include <gtest/gtest.h>
#include <cmath>

// Include the biofilm kinetics header (for KineticsDiagnostics, KineticsStats)
#include "defineKinetics.hh"

// ========================== KineticsDiagnostics ==========================

TEST(BiofilmDiagnostics, ResetClearsAll) {
    KineticsDiagnostics::total_biomass_produced = 999.0;
    KineticsDiagnostics::total_DOC_consumed = 999.0;
    KineticsDiagnostics::total_iterations = 999;
    KineticsDiagnostics::total_kinetics_calls = 999;

    KineticsDiagnostics::resetAll();

    EXPECT_DOUBLE_EQ(KineticsDiagnostics::total_biomass_produced, 0.0);
    EXPECT_DOUBLE_EQ(KineticsDiagnostics::total_DOC_consumed, 0.0);
    EXPECT_EQ(KineticsDiagnostics::total_iterations, 0);
    EXPECT_EQ(KineticsDiagnostics::total_kinetics_calls, 0);
}

TEST(BiofilmDiagnostics, RecordIterationAccumulates) {
    KineticsDiagnostics::resetAll();

    KineticsDiagnostics::recordIteration(1.0, -0.5);
    KineticsDiagnostics::recordIteration(2.0, -1.0);

    EXPECT_DOUBLE_EQ(KineticsDiagnostics::total_biomass_produced, 3.0);
    EXPECT_DOUBLE_EQ(KineticsDiagnostics::total_DOC_consumed, 1.5);
    EXPECT_EQ(KineticsDiagnostics::total_kinetics_calls, 2);
}

TEST(BiofilmDiagnostics, IncrementIterationCounter) {
    KineticsDiagnostics::resetAll();
    KineticsDiagnostics::incrementIteration();
    KineticsDiagnostics::incrementIteration();
    KineticsDiagnostics::incrementIteration();
    EXPECT_EQ(KineticsDiagnostics::total_iterations, 3);
}

// ========================== KineticsStats ==========================

TEST(BiofilmStats, ResetClearsAll) {
    KineticsStats::iter_total_calls = 999;
    KineticsStats::iter_cells_with_biomass = 999;
    KineticsStats::resetIteration();
    EXPECT_EQ(KineticsStats::iter_total_calls, 0);
    EXPECT_EQ(KineticsStats::iter_cells_with_biomass, 0);
    EXPECT_EQ(KineticsStats::iter_cells_with_growth, 0);
    EXPECT_EQ(KineticsStats::iter_cells_limited, 0);
    EXPECT_DOUBLE_EQ(KineticsStats::iter_sum_dB, 0.0);
    EXPECT_DOUBLE_EQ(KineticsStats::iter_sum_dDOC, 0.0);
    EXPECT_DOUBLE_EQ(KineticsStats::iter_max_biomass, 0.0);
    EXPECT_DOUBLE_EQ(KineticsStats::iter_max_dB, 0.0);
}

TEST(BiofilmStats, AccumulateCountsCells) {
    KineticsStats::resetIteration();

    // Biomass above MIN_BIOMASS threshold
    KineticsStats::accumulate(10.0, 1.0, 0.5, -0.3, false);
    EXPECT_EQ(KineticsStats::iter_total_calls, 1);
    EXPECT_EQ(KineticsStats::iter_cells_with_biomass, 1);
    EXPECT_EQ(KineticsStats::iter_cells_with_growth, 1);
    EXPECT_EQ(KineticsStats::iter_cells_limited, 0);
}

TEST(BiofilmStats, AccumulateIgnoresLowBiomass) {
    KineticsStats::resetIteration();

    // Biomass below MIN_BIOMASS (0.1 for biofilm)
    KineticsStats::accumulate(0.01, 1.0, 0.0, 0.0, false);
    EXPECT_EQ(KineticsStats::iter_total_calls, 1);
    EXPECT_EQ(KineticsStats::iter_cells_with_biomass, 0);
}

TEST(BiofilmStats, AccumulateTracksLimitation) {
    KineticsStats::resetIteration();
    KineticsStats::accumulate(10.0, 1.0, 0.5, -0.3, true);
    EXPECT_EQ(KineticsStats::iter_cells_limited, 1);
}

TEST(BiofilmStats, AccumulateTracksMaxBiomass) {
    KineticsStats::resetIteration();
    KineticsStats::accumulate(5.0, 1.0, 0.1, -0.1, false);
    KineticsStats::accumulate(20.0, 1.0, 0.2, -0.2, false);
    KineticsStats::accumulate(3.0, 1.0, 0.05, -0.05, false);
    EXPECT_DOUBLE_EQ(KineticsStats::iter_max_biomass, 20.0);
}

TEST(BiofilmStats, AccumulateTracksMaxGrowthRate) {
    KineticsStats::resetIteration();
    KineticsStats::accumulate(10.0, 1.0, 0.1, -0.1, false);
    KineticsStats::accumulate(10.0, 1.0, 0.5, -0.5, false);
    KineticsStats::accumulate(10.0, 1.0, 0.3, -0.3, false);
    EXPECT_DOUBLE_EQ(KineticsStats::iter_max_dB, 0.5);
}

TEST(BiofilmStats, AccumulateTracksMinDOC) {
    KineticsStats::resetIteration();
    KineticsStats::accumulate(10.0, 0.5, 0.1, -0.1, false);
    KineticsStats::accumulate(10.0, 0.01, 0.1, -0.1, false);
    KineticsStats::accumulate(10.0, 0.1, 0.1, -0.1, false);
    EXPECT_DOUBLE_EQ(KineticsStats::iter_min_DOC, 0.01);
}

TEST(BiofilmStats, GetStatsReturnsCorrectValues) {
    KineticsStats::resetIteration();
    KineticsStats::accumulate(10.0, 0.5, 0.3, -0.2, false);
    KineticsStats::accumulate(20.0, 0.1, 0.8, -0.6, false);

    long cells_b, cells_g;
    double sum_dB, max_B, max_dB, min_DOC;
    KineticsStats::getStats(cells_b, cells_g, sum_dB, max_B, max_dB, min_DOC);

    EXPECT_EQ(cells_b, 2);
    EXPECT_EQ(cells_g, 2);
    EXPECT_NEAR(sum_dB, 1.1, 1e-10);
    EXPECT_DOUBLE_EQ(max_B, 20.0);
    EXPECT_DOUBLE_EQ(max_dB, 0.8);
    EXPECT_DOUBLE_EQ(min_DOC, 0.1);
}

TEST(BiofilmStats, GetLimitedCellsWorks) {
    KineticsStats::resetIteration();
    KineticsStats::accumulate(10.0, 1.0, 0.3, -0.2, true);
    KineticsStats::accumulate(10.0, 1.0, 0.3, -0.2, false);
    KineticsStats::accumulate(10.0, 1.0, 0.3, -0.2, true);
    EXPECT_EQ(KineticsStats::getLimitedCells(), 2);
}

TEST(BiofilmStats, FourArgAccumulateDefaultsNotLimited) {
    KineticsStats::resetIteration();
    KineticsStats::accumulate(10.0, 1.0, 0.3, -0.2);
    EXPECT_EQ(KineticsStats::iter_cells_limited, 0);
}

// ========================== End-to-end mass balance via kinetics call ==========================

TEST(BiofilmMassBalance, KineticsCallUpdatesTracking) {
    KineticsDiagnostics::resetAll();
    KineticsStats::resetIteration();

    std::vector<double> B = {10.0};
    std::vector<double> C = {1.0};
    std::vector<double> subsR(2, 0.0), bioR(1, 0.0);

    defineRxnKinetics(B, C, subsR, bioR, 1);

    // After one kinetics call, diagnostics should have recorded something
    EXPECT_GT(KineticsDiagnostics::total_kinetics_calls, 0);
    // Biomass should have been produced
    EXPECT_GT(KineticsDiagnostics::total_biomass_produced, 0.0);
    // DOC should have been consumed
    EXPECT_GT(KineticsDiagnostics::total_DOC_consumed, 0.0);

    // Stats should reflect one active cell
    EXPECT_EQ(KineticsStats::iter_cells_with_biomass, 1);
}

TEST(BiofilmMassBalance, YieldConsistency) {
    KineticsDiagnostics::resetAll();

    // Run many calls and check yield consistency
    for (int i = 0; i < 100; ++i) {
        std::vector<double> B = {10.0};
        std::vector<double> C = {1.0};
        std::vector<double> subsR(2, 0.0), bioR(1, 0.0);
        defineRxnKinetics(B, C, subsR, bioR, 1);
    }

    // Over many calls: total_biomass_produced / total_DOC_consumed ~ Y
    if (KineticsDiagnostics::total_DOC_consumed > 0) {
        double effective_Y = KineticsDiagnostics::total_biomass_produced /
                            KineticsDiagnostics::total_DOC_consumed;
        // Should be close to Y (0.4) but not exact due to decay
        EXPECT_GT(effective_Y, 0.0);
        EXPECT_LT(effective_Y, KineticParams::Y + 0.1);
    }
}

// ========================== Abiotic kinetics stats ==========================

#include "defineAbioticKinetics.hh"

TEST(AbioticStats, ResetClearsAll) {
    AbioticKineticsStats::iter_total_calls = 999;
    AbioticKineticsStats::iter_cells_reacting = 999;
    AbioticKineticsStats::iter_total_reaction = 999.0;

    AbioticKineticsStats::resetIteration();

    EXPECT_EQ(AbioticKineticsStats::iter_total_calls, 0);
    EXPECT_EQ(AbioticKineticsStats::iter_cells_reacting, 0);
    EXPECT_DOUBLE_EQ(AbioticKineticsStats::iter_total_reaction, 0.0);
}

TEST(AbioticStats, AccumulateCountsReactingCells) {
    AbioticKineticsStats::resetIteration();
    AbioticKineticsStats::accumulate(-1e-3);  // non-zero = reacting
    AbioticKineticsStats::accumulate(0.0);    // zero = not reacting
    AbioticKineticsStats::accumulate(-2e-3);  // reacting

    EXPECT_EQ(AbioticKineticsStats::iter_total_calls, 3);
    EXPECT_EQ(AbioticKineticsStats::iter_cells_reacting, 2);
}

TEST(AbioticStats, TotalReactionSums) {
    AbioticKineticsStats::resetIteration();
    AbioticKineticsStats::accumulate(-1.0);
    AbioticKineticsStats::accumulate(-2.0);
    EXPECT_NEAR(AbioticKineticsStats::iter_total_reaction, -3.0, 1e-10);
}
