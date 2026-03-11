// Unit tests for defineRxnKinetics (planktonic bacteria variant)
// Uses a minimal plb shim so the header can compile without Palabos.

#include "plb_shim.h"
#include <gtest/gtest.h>

// Include the planktonic kinetics header
#include "defineKinetics_planktonic.hh"

// ---------- Basic growth tests ----------

TEST(PlanktonicKinetics, NoBiomassNoReaction) {
    std::vector<double> B = {0.0};
    std::vector<double> C = {1.0};
    std::vector<double> subsR(2, 0.0), bioR(1, 0.0);
    defineRxnKinetics(B, C, subsR, bioR, 1);
    EXPECT_DOUBLE_EQ(subsR[0], 0.0);
    EXPECT_DOUBLE_EQ(bioR[0], 0.0);
}

TEST(PlanktonicKinetics, HighSubstrateGivesGrowth) {
    std::vector<double> B = {1.0};   // above planktonic MIN_BIOMASS (0.01)
    std::vector<double> C = {1.0};
    std::vector<double> subsR(2, 0.0), bioR(1, 0.0);
    defineRxnKinetics(B, C, subsR, bioR, 1);
    EXPECT_GT(bioR[0], 0.0);
    EXPECT_LT(subsR[0], 0.0);
}

TEST(PlanktonicKinetics, CO2ProducedWhenSubstrateConsumed) {
    std::vector<double> B = {1.0};
    std::vector<double> C = {1.0};
    std::vector<double> subsR(2, 0.0), bioR(1, 0.0);
    defineRxnKinetics(B, C, subsR, bioR, 1);
    EXPECT_GT(subsR[1], 0.0);  // CO2 production positive
}

// ---------- Monod saturation ----------

TEST(PlanktonicKinetics, MonodSaturationBehavior) {
    std::vector<double> B = {1.0};
    std::vector<double> C_high = {1000.0};
    std::vector<double> C_half = {KineticParams::Ks};
    std::vector<double> sR_high(2, 0.0), bR_high(1, 0.0);
    std::vector<double> sR_half(2, 0.0), bR_half(1, 0.0);

    defineRxnKinetics(B, C_high, sR_high, bR_high, 1);
    defineRxnKinetics(B, C_half, sR_half, bR_half, 1);

    EXPECT_GT(bR_high[0], bR_half[0]);
}

// ---------- Substrate clamping ----------

TEST(PlanktonicKinetics, SubstrateConsumptionClamped) {
    double doc = 1e-4;
    std::vector<double> B = {1e6};
    std::vector<double> C = {doc};
    std::vector<double> subsR(2, 0.0), bioR(1, 0.0);
    defineRxnKinetics(B, C, subsR, bioR, 1);

    double max_allowed = doc * KineticParams::MAX_DOC_CONSUMPTION_FRACTION
                         / KineticParams::dt_kinetics;
    EXPECT_LE(-subsR[0], max_allowed + 1e-20);
}

// ---------- Zero substrate ----------

TEST(PlanktonicKinetics, ZeroSubstrateGivesDecayOnly) {
    std::vector<double> B = {1.0};
    std::vector<double> C = {0.0};
    std::vector<double> subsR(2, 0.0), bioR(1, 0.0);
    defineRxnKinetics(B, C, subsR, bioR, 1);
    EXPECT_LE(bioR[0], 0.0);
    EXPECT_DOUBLE_EQ(subsR[0], 0.0);
}

// ---------- No NaN/Inf ----------

TEST(PlanktonicKinetics, NoNanOrInfOutputs) {
    std::vector<double> B = {1.0};
    std::vector<double> C = {1.0};
    std::vector<double> subsR(2, 0.0), bioR(1, 0.0);
    defineRxnKinetics(B, C, subsR, bioR, 1);
    EXPECT_FALSE(std::isnan(subsR[0]));
    EXPECT_FALSE(std::isnan(subsR[1]));
    EXPECT_FALSE(std::isnan(bioR[0]));
    EXPECT_FALSE(std::isinf(subsR[0]));
    EXPECT_FALSE(std::isinf(bioR[0]));
}

// ---------- Empty vectors ----------

TEST(PlanktonicKinetics, EmptyVectorsNoAction) {
    std::vector<double> B, C, subsR, bioR;
    defineRxnKinetics(B, C, subsR, bioR, 1);
}

// ---------- Parameter validation ----------

TEST(PlanktonicKinetics, ParameterValidationPasses) {
    EXPECT_TRUE(KineticsValidation::validateParameters());
}

// ---------- Input validation ----------

TEST(PlanktonicKinetics, InputValidationDetectsEmptyVectors) {
    std::vector<double> B, C, subsR(1, 0.0), bioR(1, 0.0);
    EXPECT_FALSE(KineticsValidation::validateInputs(B, C, subsR, bioR));
}

TEST(PlanktonicKinetics, InputValidationPassesForGoodInputs) {
    std::vector<double> B = {1.0}, C = {0.5};
    std::vector<double> subsR(2, 0.0), bioR(1, 0.0);
    EXPECT_TRUE(KineticsValidation::validateInputs(B, C, subsR, bioR));
}

// ---------- Planktonic-specific parameters ----------

TEST(PlanktonicKinetics, PlanktonicParamsDifferFromBiofilm) {
    // Planktonic mu_max should be 0.5 (biofilm is 1.0)
    EXPECT_DOUBLE_EQ(KineticParams::mu_max, 0.5);
    // Planktonic MIN_BIOMASS should be 0.01 (biofilm is 0.1)
    EXPECT_DOUBLE_EQ(KineticParams::MIN_BIOMASS, 0.01);
    // Planktonic k_decay should be 1e-7 (biofilm is 1e-9)
    EXPECT_DOUBLE_EQ(KineticParams::k_decay, 1.0e-7);
}

// ---------- Statistics ----------

TEST(PlanktonicKinetics, StatsResetAndAccumulate) {
    KineticsStats::resetIteration();
    EXPECT_EQ(KineticsStats::iter_total_calls, 0);
    EXPECT_EQ(KineticsStats::iter_cells_with_biomass, 0);
    EXPECT_EQ(KineticsStats::iter_cells_decaying, 0);

    KineticsStats::accumulate(1.0, 0.5, 0.1, -0.3, false);
    EXPECT_EQ(KineticsStats::iter_total_calls, 1);
    EXPECT_EQ(KineticsStats::iter_cells_with_biomass, 1);
    EXPECT_EQ(KineticsStats::iter_cells_with_growth, 1);

    KineticsStats::accumulate(1.0, 0.5, -0.01, 0.0, false);
    EXPECT_EQ(KineticsStats::iter_cells_decaying, 1);
}

TEST(PlanktonicKinetics, AvgBiomassCalculation) {
    KineticsStats::resetIteration();
    KineticsStats::accumulate(2.0, 1.0, 0.1, -0.1, false);
    KineticsStats::accumulate(4.0, 1.0, 0.2, -0.2, false);
    EXPECT_NEAR(KineticsStats::getAvgBiomass(), 3.0, 1e-10);
}

// ---------- Mass balance ----------

TEST(PlanktonicKinetics, MassBalanceYieldRelation) {
    std::vector<double> B = {1.0};
    std::vector<double> C = {1.0};
    std::vector<double> subsR(2, 0.0), bioR(1, 0.0);
    defineRxnKinetics(B, C, subsR, bioR, 1);

    double doc_consumed = -subsR[0];
    double biomass_growth = bioR[0];
    double expected_growth = doc_consumed * KineticParams::Y - KineticParams::k_decay * B[0];
    EXPECT_NEAR(biomass_growth, expected_growth, 1e-6);
}

// ---------- Diagnostics ----------

TEST(PlanktonicKinetics, DiagnosticsResetAndRecord) {
    KineticsDiagnostics::resetAll();
    EXPECT_DOUBLE_EQ(KineticsDiagnostics::total_biomass_produced, 0.0);
    EXPECT_DOUBLE_EQ(KineticsDiagnostics::total_DOC_consumed, 0.0);
    EXPECT_DOUBLE_EQ(KineticsDiagnostics::total_CO2_produced, 0.0);

    KineticsDiagnostics::recordIteration(0.5, -0.3, 0.3);
    EXPECT_DOUBLE_EQ(KineticsDiagnostics::total_biomass_produced, 0.5);
    EXPECT_DOUBLE_EQ(KineticsDiagnostics::total_DOC_consumed, 0.3);
    EXPECT_DOUBLE_EQ(KineticsDiagnostics::total_CO2_produced, 0.3);
}
