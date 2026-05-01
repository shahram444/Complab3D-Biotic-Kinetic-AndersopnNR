// Extended unit tests for defineRxnKinetics (planktonic variant)
// Covers: dilution factor, planktonic-specific parameters, diagnostics,
// multi-substrate CO2 tracking, and comparison with biofilm kinetics.

#include "plb_shim.h"
#include <gtest/gtest.h>
#include <cmath>
#include <vector>

#include "defineKinetics_planktonic.hh"

// ============================================================================
// PLANKTONIC-SPECIFIC PARAMETER TESTS
// ============================================================================

TEST(PlanktonicKineticsExt, DilutionFactorExists) {
    EXPECT_GT(KineticParams::PLANKTONIC_DILUTION_FACTOR, 0.0);
    EXPECT_LE(KineticParams::PLANKTONIC_DILUTION_FACTOR, 1.0);
}

TEST(PlanktonicKineticsExt, PlanktonicDecayRate) {
    // Planktonic k_decay is typically different from biofilm
    EXPECT_GT(KineticParams::k_decay, 0.0);
}

TEST(PlanktonicKineticsExt, PlanktonicMinBiomass) {
    EXPECT_GT(KineticParams::MIN_BIOMASS, 0.0);
}

// ============================================================================
// GROWTH AND DECAY DETAILED TESTS
// ============================================================================

TEST(PlanktonicKineticsExt, DecayOnlyWithZeroSubstrate) {
    double B0 = 10.0;
    std::vector<double> B = {B0};
    std::vector<double> C = {0.0};
    std::vector<double> subsR(2, 0.0), bioR(1, 0.0);
    defineRxnKinetics(B, C, subsR, bioR, 1);

    // Decay should be negative
    EXPECT_LE(bioR[0], 0.0);
    // Expected: -k_decay * B
    double expected = -KineticParams::k_decay * B0;
    EXPECT_NEAR(bioR[0], expected, std::abs(expected) * 0.01 + 1e-15);
}

TEST(PlanktonicKineticsExt, GrowthAtSaturation) {
    double B0 = 10.0;
    std::vector<double> B = {B0};
    std::vector<double> C = {1e6};  // >> Ks
    std::vector<double> subsR(2, 0.0), bioR(1, 0.0);
    defineRxnKinetics(B, C, subsR, bioR, 1);

    double expected_max = (KineticParams::mu_max - KineticParams::k_decay) * B0;
    EXPECT_NEAR(bioR[0], expected_max, std::abs(expected_max) * 0.01);
}

TEST(PlanktonicKineticsExt, GrowthProportionalToBiomass) {
    std::vector<double> B1 = {5.0}, B2 = {15.0};
    std::vector<double> C = {1.0};
    std::vector<double> sR1(2, 0.0), bR1(1, 0.0);
    std::vector<double> sR2(2, 0.0), bR2(1, 0.0);

    defineRxnKinetics(B1, C, sR1, bR1, 1);
    defineRxnKinetics(B2, C, sR2, bR2, 1);

    // Growth rate should be proportional to biomass
    EXPECT_NEAR(bR2[0] / bR1[0], 3.0, 0.1);
}

// ============================================================================
// CO2 TRACKING TESTS
// ============================================================================

TEST(PlanktonicKineticsExt, CO2ProducedWithGrowth) {
    std::vector<double> B = {10.0};
    std::vector<double> C = {1.0};
    std::vector<double> subsR(2, 0.0), bioR(1, 0.0);
    defineRxnKinetics(B, C, subsR, bioR, 1);

    EXPECT_GT(subsR[1], 0.0);  // CO2 production positive
    EXPECT_LT(subsR[0], 0.0);  // DOC consumption negative
}

TEST(PlanktonicKineticsExt, NoCO2WithoutBiomass) {
    std::vector<double> B = {0.0};
    std::vector<double> C = {1.0};
    std::vector<double> subsR(2, 0.0), bioR(1, 0.0);
    defineRxnKinetics(B, C, subsR, bioR, 1);

    EXPECT_DOUBLE_EQ(subsR[1], 0.0);
}

// ============================================================================
// MULTI-STEP TIME INTEGRATION TESTS
// ============================================================================

TEST(PlanktonicKineticsExt, TimeSteppingStability) {
    double B = 10.0;
    double DOC = 1.0;
    double dt = KineticParams::dt_kinetics;

    for (int step = 0; step < 5000; ++step) {
        std::vector<double> Bvec = {B};
        std::vector<double> Cvec = {DOC};
        std::vector<double> subsR(2, 0.0), bioR(1, 0.0);
        defineRxnKinetics(Bvec, Cvec, subsR, bioR, 1);

        B += bioR[0] * dt;
        DOC += subsR[0] * dt;

        EXPECT_GE(B, -1e-10) << "Negative biomass at step " << step;
        EXPECT_GE(DOC, -1e-10) << "Negative DOC at step " << step;
        if (B < 0) B = 0;
        if (DOC < 0) DOC = 0;
        EXPECT_FALSE(std::isnan(B));
    }
}

// ============================================================================
// SUBSTRATE LIMITATION CLAMPING TESTS
// ============================================================================

TEST(PlanktonicKineticsExt, SubstrateClampingWorks) {
    double doc = 1e-6;
    std::vector<double> B = {1e6};
    std::vector<double> C = {doc};
    std::vector<double> subsR(2, 0.0), bioR(1, 0.0);
    defineRxnKinetics(B, C, subsR, bioR, 1);

    double max_allowed = doc * KineticParams::MAX_DOC_CONSUMPTION_FRACTION
                         / KineticParams::dt_kinetics;
    EXPECT_LE(-subsR[0], max_allowed + 1e-25);
}

// ============================================================================
// EXTREME INPUTS
// ============================================================================

TEST(PlanktonicKineticsExt, VeryLargeBiomass) {
    std::vector<double> B = {1e10};
    std::vector<double> C = {1.0};
    std::vector<double> subsR(2, 0.0), bioR(1, 0.0);
    defineRxnKinetics(B, C, subsR, bioR, 1);

    EXPECT_FALSE(std::isnan(bioR[0]));
    EXPECT_FALSE(std::isinf(bioR[0]));
}

TEST(PlanktonicKineticsExt, VerySmallBiomass) {
    std::vector<double> B = {1e-20};
    std::vector<double> C = {1.0};
    std::vector<double> subsR(2, 0.0), bioR(1, 0.0);
    defineRxnKinetics(B, C, subsR, bioR, 1);

    EXPECT_FALSE(std::isnan(bioR[0]));
    // Below MIN_BIOMASS, no reaction
    EXPECT_NEAR(bioR[0], 0.0, 1e-15);
}

// ============================================================================
// STATISTICS EXTENDED TESTS
// ============================================================================

TEST(PlanktonicKineticsExt, StatsDecayingCells) {
    KineticsStats::resetIteration();
    KineticsStats::accumulate(10.0, 0.0, -0.01, 0.0, false);  // decaying
    KineticsStats::accumulate(10.0, 1.0, 0.5, -0.3, false);    // growing
    EXPECT_EQ(KineticsStats::getDecayingCells(), 1);
}

TEST(PlanktonicKineticsExt, StatsAvgBiomass) {
    KineticsStats::resetIteration();
    KineticsStats::accumulate(10.0, 1.0, 0.1, -0.05, false);
    KineticsStats::accumulate(20.0, 1.0, 0.2, -0.1, false);
    double avg = KineticsStats::getAvgBiomass();
    EXPECT_NEAR(avg, 15.0, 1e-10);
}

// ============================================================================
// DIAGNOSTICS TESTS
// ============================================================================

TEST(PlanktonicKineticsExt, DiagnosticsAccumulation) {
    KineticsDiagnostics::resetAll();
    for (int i = 0; i < 50; ++i) {
        KineticsDiagnostics::recordIteration(0.1, -0.05, 0.03);
        KineticsDiagnostics::incrementIteration();
    }
    EXPECT_NO_FATAL_FAILURE(KineticsDiagnostics::resetAll());
}

// ============================================================================
// INPUT VALIDATION EXTENDED TESTS
// ============================================================================

TEST(PlanktonicKineticsExt, ValidInputsPasses) {
    std::vector<double> B = {10.0};
    std::vector<double> C = {1.0};
    std::vector<double> subsR(2, 0.0), bioR(1, 0.0);
    EXPECT_TRUE(KineticsValidation::validateInputs(B, C, subsR, bioR));
}

TEST(PlanktonicKineticsExt, EmptyInputsFails) {
    std::vector<double> B, C, subsR, bioR;
    EXPECT_FALSE(KineticsValidation::validateInputs(B, C, subsR, bioR));
}

TEST(PlanktonicKineticsExt, MismatchedSizesFails) {
    std::vector<double> B = {10.0};
    std::vector<double> C = {1.0};
    std::vector<double> subsR(2, 0.0);
    std::vector<double> bioR;  // empty, mismatched
    EXPECT_FALSE(KineticsValidation::validateInputs(B, C, subsR, bioR));
}

// ============================================================================
// MONOD CURVE SHAPE
// ============================================================================

TEST(PlanktonicKineticsExt, MonodHalfSaturation) {
    using namespace KineticParams;
    double B0 = 10.0;
    std::vector<double> B = {B0};

    // At Ks, monod = 0.5, but clamping may apply at small DOC
    std::vector<double> C = {Ks};
    std::vector<double> subsR(2, 0.0), bioR(1, 0.0);
    defineRxnKinetics(B, C, subsR, bioR, 1);

    double DOC = Ks;
    double mu = mu_max * 0.5;
    double dDOC_unclamped = -mu * B0 / Y;
    double max_consumption_rate = DOC * MAX_DOC_CONSUMPTION_FRACTION / dt_kinetics;
    double expected;
    if (-dDOC_unclamped > max_consumption_rate) {
        double actual_mu = max_consumption_rate * Y / B0;
        expected = (actual_mu - k_decay) * B0;
    } else {
        expected = (mu - k_decay) * B0;
    }
    EXPECT_NEAR(bioR[0], expected, std::abs(expected) * 0.05);
}

// ============================================================================
// DETERMINISM TEST
// ============================================================================

TEST(PlanktonicKineticsExt, DeterministicOutput) {
    std::vector<double> B = {10.0};
    std::vector<double> C = {1.0};

    std::vector<double> sR1(2, 0.0), bR1(1, 0.0);
    defineRxnKinetics(B, C, sR1, bR1, 1);

    std::vector<double> sR2(2, 0.0), bR2(1, 0.0);
    defineRxnKinetics(B, C, sR2, bR2, 1);

    EXPECT_DOUBLE_EQ(sR1[0], sR2[0]);
    EXPECT_DOUBLE_EQ(sR1[1], sR2[1]);
    EXPECT_DOUBLE_EQ(bR1[0], bR2[0]);
}
