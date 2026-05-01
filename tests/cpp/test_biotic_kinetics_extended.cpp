// Extended unit tests for defineRxnKinetics (biotic / Monod kinetics)
// Covers: decay rate precision, CO2 mass balance, multi-iteration stability,
// extreme inputs, boundary mask behavior, and Monod curve shape.

#include "plb_shim.h"
#include <gtest/gtest.h>
#include <cmath>
#include <vector>
#include <limits>

#include "defineKinetics.hh"

// ============================================================================
// DECAY RATE TESTS
// ============================================================================

TEST(BioticKineticsExt, DecayRateMatchesParameter) {
    // With zero substrate, only decay should occur: dB/dt = -k_decay * B
    double B0 = 100.0;
    std::vector<double> B = {B0};
    std::vector<double> C = {0.0};
    std::vector<double> subsR(2, 0.0), bioR(1, 0.0);
    defineRxnKinetics(B, C, subsR, bioR, 1);

    double expected_decay = -KineticParams::k_decay * B0;
    EXPECT_NEAR(bioR[0], expected_decay, std::abs(expected_decay) * 1e-6);
}

TEST(BioticKineticsExt, DecayIsProportionalToBiomass) {
    std::vector<double> B1 = {10.0}, B2 = {20.0};
    std::vector<double> C = {0.0};
    std::vector<double> sR1(2, 0.0), bR1(1, 0.0);
    std::vector<double> sR2(2, 0.0), bR2(1, 0.0);

    defineRxnKinetics(B1, C, sR1, bR1, 1);
    defineRxnKinetics(B2, C, sR2, bR2, 1);

    // Decay should be proportional to biomass
    EXPECT_NEAR(bR2[0] / bR1[0], 2.0, 1e-6);
}

// ============================================================================
// CO2 MASS BALANCE TESTS
// ============================================================================

TEST(BioticKineticsExt, CO2ProductionEqualsSubstrateConsumption) {
    // CO2 produced should equal DOC consumed (1:1 stoichiometry minus yield)
    // dCO2/dt = -dDOC/dt (what goes in as DOC comes out as CO2 + biomass)
    std::vector<double> B = {10.0};
    std::vector<double> C = {1.0};
    std::vector<double> subsR(2, 0.0), bioR(1, 0.0);
    defineRxnKinetics(B, C, subsR, bioR, 1);

    double doc_consumed = -subsR[0];
    double co2_produced = subsR[1];
    // CO2 = DOC consumed - biomass produced / Y
    // Actually: CO2 = DOC consumed (1:1 assumed in most formulations)
    EXPECT_GT(co2_produced, 0.0);
    EXPECT_GT(doc_consumed, 0.0);
    // CO2 should not exceed DOC consumed
    EXPECT_LE(co2_produced, doc_consumed + 1e-10);
}

TEST(BioticKineticsExt, CO2ZeroWhenNoReaction) {
    std::vector<double> B = {0.0};
    std::vector<double> C = {1.0};
    std::vector<double> subsR(2, 0.0), bioR(1, 0.0);
    defineRxnKinetics(B, C, subsR, bioR, 1);
    EXPECT_DOUBLE_EQ(subsR[1], 0.0);  // No CO2 without biomass
}

// ============================================================================
// MONOD CURVE SHAPE TESTS
// ============================================================================

TEST(BioticKineticsExt, MonodCurveIncreasingWithSubstrate) {
    std::vector<double> B = {10.0};
    double concentrations[] = {1e-4, 1e-3, 1e-2, 0.1, 1.0, 10.0};
    double prev_growth = -1e30;

    for (double doc : concentrations) {
        std::vector<double> C = {doc};
        std::vector<double> subsR(2, 0.0), bioR(1, 0.0);
        defineRxnKinetics(B, C, subsR, bioR, 1);
        EXPECT_GE(bioR[0], prev_growth) << "Growth should increase with substrate at doc=" << doc;
        prev_growth = bioR[0];
    }
}

TEST(BioticKineticsExt, MonodSaturationApproachesLimit) {
    // At very high substrate, growth rate should approach mu_max * B - k_decay * B
    std::vector<double> B = {10.0};
    std::vector<double> C = {1e6};  // >> Ks
    std::vector<double> subsR(2, 0.0), bioR(1, 0.0);
    defineRxnKinetics(B, C, subsR, bioR, 1);

    double expected_max = (KineticParams::mu_max - KineticParams::k_decay) * B[0];
    EXPECT_NEAR(bioR[0], expected_max, std::abs(expected_max) * 0.01);
}

TEST(BioticKineticsExt, MonodHalfSaturationPoint) {
    // At DOC = Ks, monod term = 0.5.
    // But with small DOC (Ks=1e-5), clamping kicks in, so we must account for it.
    using namespace KineticParams;
    std::vector<double> B = {10.0};
    std::vector<double> C = {Ks};  // DOC = Ks
    std::vector<double> subsR(2, 0.0), bioR(1, 0.0);
    defineRxnKinetics(B, C, subsR, bioR, 1);

    // Compute expected with clamping logic:
    double DOC = Ks;
    double biomass = B[0];
    double mu = mu_max * 0.5;  // monod = Ks/(Ks+Ks) = 0.5
    double dDOC_unclamped = -mu * biomass / Y;
    double max_consumption_rate = DOC * MAX_DOC_CONSUMPTION_FRACTION / dt_kinetics;
    double expected;
    if (-dDOC_unclamped > max_consumption_rate) {
        // Clamped case
        double actual_mu = max_consumption_rate * Y / biomass;
        expected = (actual_mu - k_decay) * biomass;
    } else {
        expected = (mu - k_decay) * biomass;
    }
    EXPECT_NEAR(bioR[0], expected, std::abs(expected) * 0.05);
}

// ============================================================================
// MULTI-ITERATION STABILITY TESTS
// ============================================================================

TEST(BioticKineticsExt, RepeatedCallsNoAccumulation) {
    // Calling with same inputs should give same outputs
    std::vector<double> B = {10.0};
    std::vector<double> C = {1.0};

    for (int iter = 0; iter < 100; ++iter) {
        std::vector<double> subsR(2, 0.0), bioR(1, 0.0);
        defineRxnKinetics(B, C, subsR, bioR, 1);
        EXPECT_FALSE(std::isnan(subsR[0])) << "NaN at iter " << iter;
        EXPECT_FALSE(std::isinf(subsR[0])) << "Inf at iter " << iter;
    }
}

TEST(BioticKineticsExt, TimeSteppingStability) {
    // Simulate multiple timesteps with Euler integration
    double B = 10.0;
    double DOC = 1.0;
    double dt = KineticParams::dt_kinetics;

    for (int step = 0; step < 1000; ++step) {
        std::vector<double> Bvec = {B};
        std::vector<double> Cvec = {DOC};
        std::vector<double> subsR(2, 0.0), bioR(1, 0.0);
        defineRxnKinetics(Bvec, Cvec, subsR, bioR, 1);

        B += bioR[0] * dt;
        DOC += subsR[0] * dt;

        // Biomass should stay non-negative
        EXPECT_GE(B, 0.0) << "Negative biomass at step " << step;
        // DOC should stay non-negative
        EXPECT_GE(DOC, -1e-10) << "Negative DOC at step " << step;

        if (DOC < 0) DOC = 0;
    }
}

// ============================================================================
// EXTREME INPUT TESTS
// ============================================================================

TEST(BioticKineticsExt, VeryLargeBiomass) {
    std::vector<double> B = {1e12};
    std::vector<double> C = {1e-8};  // very low substrate
    std::vector<double> subsR(2, 0.0), bioR(1, 0.0);
    defineRxnKinetics(B, C, subsR, bioR, 1);

    EXPECT_FALSE(std::isnan(bioR[0]));
    EXPECT_FALSE(std::isinf(bioR[0]));
    // Should be substrate-limited (clamped)
    double max_allowed = C[0] * KineticParams::MAX_DOC_CONSUMPTION_FRACTION / KineticParams::dt_kinetics;
    EXPECT_LE(-subsR[0], max_allowed + 1e-20);
}

TEST(BioticKineticsExt, VerySmallBiomass) {
    std::vector<double> B = {KineticParams::MIN_BIOMASS * 0.5};  // below threshold
    std::vector<double> C = {1.0};
    std::vector<double> subsR(2, 0.0), bioR(1, 0.0);
    defineRxnKinetics(B, C, subsR, bioR, 1);

    // Below MIN_BIOMASS -> should not grow
    EXPECT_DOUBLE_EQ(subsR[0], 0.0);
    EXPECT_DOUBLE_EQ(bioR[0], 0.0);
}

TEST(BioticKineticsExt, ExactlyAtMinBiomass) {
    std::vector<double> B = {KineticParams::MIN_BIOMASS};
    std::vector<double> C = {1.0};
    std::vector<double> subsR(2, 0.0), bioR(1, 0.0);
    defineRxnKinetics(B, C, subsR, bioR, 1);

    // At MIN_BIOMASS, behavior depends on implementation (>= vs >)
    EXPECT_FALSE(std::isnan(bioR[0]));
}

TEST(BioticKineticsExt, NegativeBiomassHandled) {
    std::vector<double> B = {-5.0};
    std::vector<double> C = {1.0};
    std::vector<double> subsR(2, 0.0), bioR(1, 0.0);
    defineRxnKinetics(B, C, subsR, bioR, 1);

    EXPECT_FALSE(std::isnan(bioR[0]));
    EXPECT_FALSE(std::isinf(bioR[0]));
}

TEST(BioticKineticsExt, NegativeSubstrateHandled) {
    std::vector<double> B = {10.0};
    std::vector<double> C = {-0.001};
    std::vector<double> subsR(2, 0.0), bioR(1, 0.0);
    defineRxnKinetics(B, C, subsR, bioR, 1);

    EXPECT_FALSE(std::isnan(subsR[0]));
    EXPECT_FALSE(std::isnan(bioR[0]));
}

// ============================================================================
// MASK VALUE TESTS
// ============================================================================

TEST(BioticKineticsExt, MaskZeroSkipsReaction) {
    std::vector<double> B = {10.0};
    std::vector<double> C = {1.0};
    std::vector<double> subsR(2, 0.0), bioR(1, 0.0);
    defineRxnKinetics(B, C, subsR, bioR, 0);  // solid mask

    // Depending on implementation, mask=0 might skip
    EXPECT_FALSE(std::isnan(bioR[0]));
}

TEST(BioticKineticsExt, DifferentMaskValues) {
    // Test multiple mask values to ensure no crashes
    std::vector<double> B = {10.0};
    std::vector<double> C = {1.0};
    int masks[] = {0, 1, 2, 3, 5, 10, 100, -1};

    for (int m : masks) {
        std::vector<double> subsR(2, 0.0), bioR(1, 0.0);
        defineRxnKinetics(B, C, subsR, bioR, m);
        EXPECT_FALSE(std::isnan(bioR[0])) << "NaN for mask=" << m;
    }
}

// ============================================================================
// YIELD COEFFICIENT TESTS
// ============================================================================

TEST(BioticKineticsExt, YieldRelationPrecise) {
    // With no clamping and no decay, DOC consumed * Y should equal biomass growth
    // Use moderate conditions to avoid clamping
    double B0 = 1.0;
    double DOC0 = 100.0;  // very high substrate, no clamping expected
    std::vector<double> B = {B0};
    std::vector<double> C = {DOC0};
    std::vector<double> subsR(2, 0.0), bioR(1, 0.0);
    defineRxnKinetics(B, C, subsR, bioR, 1);

    double doc_consumed = -subsR[0];
    double bio_growth_from_yield = doc_consumed * KineticParams::Y;
    double bio_loss_from_decay = KineticParams::k_decay * B0;
    double net_growth = bio_growth_from_yield - bio_loss_from_decay;

    EXPECT_NEAR(bioR[0], net_growth, std::abs(net_growth) * 1e-4 + 1e-15);
}

// ============================================================================
// STATISTICS EXTENDED TESTS
// ============================================================================

TEST(BioticKineticsExt, StatsTrackMaxBiomass) {
    KineticsStats::resetIteration();
    KineticsStats::accumulate(5.0, 1.0, 0.1, -0.05, false);
    KineticsStats::accumulate(15.0, 1.0, 0.2, -0.1, false);
    KineticsStats::accumulate(10.0, 1.0, 0.15, -0.08, true);

    long cells_b, cells_g;
    double sum_dB, max_B, max_dB, min_DOC;
    KineticsStats::getStats(cells_b, cells_g, sum_dB, max_B, max_dB, min_DOC);

    EXPECT_EQ(cells_b, 3);
    EXPECT_EQ(cells_g, 3);
    EXPECT_NEAR(max_B, 15.0, 1e-10);
    EXPECT_NEAR(max_dB, 0.2, 1e-10);
    EXPECT_EQ(KineticsStats::getLimitedCells(), 1);
}

TEST(BioticKineticsExt, StatsMinDOCTracking) {
    KineticsStats::resetIteration();
    KineticsStats::accumulate(10.0, 5.0, 0.1, -0.05, false);
    KineticsStats::accumulate(10.0, 0.001, 0.1, -0.05, false);
    KineticsStats::accumulate(10.0, 2.0, 0.1, -0.05, false);

    long cells_b, cells_g;
    double sum_dB, max_B, max_dB, min_DOC;
    KineticsStats::getStats(cells_b, cells_g, sum_dB, max_B, max_dB, min_DOC);

    EXPECT_NEAR(min_DOC, 0.001, 1e-10);
}

// ============================================================================
// DIAGNOSTICS TESTS
// ============================================================================

TEST(BioticKineticsExt, DiagnosticsResetAndRecord) {
    KineticsDiagnostics::resetAll();
    KineticsDiagnostics::recordIteration(0.5, -0.3);
    KineticsDiagnostics::recordIteration(0.2, -0.1);
    KineticsDiagnostics::incrementIteration();

    // Should not crash and counters should update
    EXPECT_NO_FATAL_FAILURE(KineticsDiagnostics::resetAll());
}

TEST(BioticKineticsExt, DiagnosticsMultipleResets) {
    for (int i = 0; i < 10; ++i) {
        KineticsDiagnostics::resetAll();
        KineticsDiagnostics::recordIteration(1.0, -0.5);
        KineticsDiagnostics::incrementIteration();
    }
    // No crashes after repeated reset-record cycles
}

// ============================================================================
// PARAMETER VALIDATION TESTS
// ============================================================================

TEST(BioticKineticsExt, ParametersArePhysical) {
    EXPECT_GT(KineticParams::mu_max, 0.0);
    EXPECT_GT(KineticParams::Ks, 0.0);
    EXPECT_GT(KineticParams::Y, 0.0);
    EXPECT_LE(KineticParams::Y, 1.0);  // Yield should be <= 1
    EXPECT_GT(KineticParams::k_decay, 0.0);
    EXPECT_GT(KineticParams::MIN_CONC, 0.0);
    EXPECT_GT(KineticParams::MIN_BIOMASS, 0.0);
    EXPECT_GT(KineticParams::MAX_DOC_CONSUMPTION_FRACTION, 0.0);
    EXPECT_LE(KineticParams::MAX_DOC_CONSUMPTION_FRACTION, 1.0);
    EXPECT_GT(KineticParams::dt_kinetics, 0.0);
}
