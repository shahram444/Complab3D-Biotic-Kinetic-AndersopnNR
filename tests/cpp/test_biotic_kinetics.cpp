// Unit tests for defineRxnKinetics (biotic / Monod kinetics)
// Uses a minimal plb shim so the header can compile without Palabos.

#include "plb_shim.h"
#include <gtest/gtest.h>

// Include the production header (from project root)
#include "defineKinetics.hh"

// ---------- Basic growth tests ----------

TEST(BioticKinetics, NoBiomassNoReaction) {
    std::vector<double> B = {0.0};   // no biomass
    std::vector<double> C = {1.0};   // plenty of substrate
    std::vector<double> subsR(2, 0.0), bioR(1, 0.0);
    defineRxnKinetics(B, C, subsR, bioR, 1);
    EXPECT_DOUBLE_EQ(subsR[0], 0.0);
    EXPECT_DOUBLE_EQ(bioR[0], 0.0);
}

TEST(BioticKinetics, HighSubstrateGivesGrowth) {
    std::vector<double> B = {10.0};  // above MIN_BIOMASS
    std::vector<double> C = {1.0};   // well above Ks
    std::vector<double> subsR(2, 0.0), bioR(1, 0.0);
    defineRxnKinetics(B, C, subsR, bioR, 1);
    // With high substrate and biomass, net growth should be positive
    EXPECT_GT(bioR[0], 0.0);
    // DOC should be consumed (negative rate)
    EXPECT_LT(subsR[0], 0.0);
}

TEST(BioticKinetics, CO2ProducedWhenSubstrateConsumed) {
    std::vector<double> B = {10.0};
    std::vector<double> C = {1.0};
    std::vector<double> subsR(2, 0.0), bioR(1, 0.0);
    defineRxnKinetics(B, C, subsR, bioR, 1);
    // CO2 production (subsR[1]) should be positive when DOC consumed
    EXPECT_GT(subsR[1], 0.0);
}

// ---------- Monod saturation ----------

TEST(BioticKinetics, MonodSaturationBehavior) {
    // At very high DOC, Monod approaches mu_max.
    // At DOC = Ks, Monod = 0.5 * mu_max.
    std::vector<double> B = {10.0};
    std::vector<double> C_high = {1000.0};  // >> Ks
    std::vector<double> C_half = {KineticParams::Ks};
    std::vector<double> subsR_high(2, 0.0), bioR_high(1, 0.0);
    std::vector<double> subsR_half(2, 0.0), bioR_half(1, 0.0);

    defineRxnKinetics(B, C_high, subsR_high, bioR_high, 1);
    defineRxnKinetics(B, C_half, subsR_half, bioR_half, 1);

    // Growth at Ks should be roughly half of growth at saturation
    // (not exact because of clamping, but directionally correct)
    EXPECT_GT(bioR_high[0], bioR_half[0]);
}

// ---------- Substrate clamping ----------

TEST(BioticKinetics, SubstrateConsumptionClamped) {
    // Even with extreme biomass, DOC consumption should not exceed
    // MAX_DOC_CONSUMPTION_FRACTION * DOC / dt.
    double doc = 1e-4;
    std::vector<double> B = {1e6};   // enormous biomass
    std::vector<double> C = {doc};
    std::vector<double> subsR(2, 0.0), bioR(1, 0.0);
    defineRxnKinetics(B, C, subsR, bioR, 1);

    double max_allowed = doc * KineticParams::MAX_DOC_CONSUMPTION_FRACTION
                         / KineticParams::dt_kinetics;
    EXPECT_LE(-subsR[0], max_allowed + 1e-20);
}

// ---------- Zero substrate ----------

TEST(BioticKinetics, ZeroSubstrateGivesDecayOnly) {
    std::vector<double> B = {10.0};
    std::vector<double> C = {0.0};
    std::vector<double> subsR(2, 0.0), bioR(1, 0.0);
    defineRxnKinetics(B, C, subsR, bioR, 1);
    // With no substrate, biomass should decay (negative dB/dt)
    EXPECT_LE(bioR[0], 0.0);
    // No DOC consumption
    EXPECT_DOUBLE_EQ(subsR[0], 0.0);
}

// ---------- No NaN/Inf ----------

TEST(BioticKinetics, NoNanOrInfOutputs) {
    std::vector<double> B = {10.0};
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

TEST(BioticKinetics, EmptyVectorsNoAction) {
    std::vector<double> B, C, subsR, bioR;
    // Should not crash
    defineRxnKinetics(B, C, subsR, bioR, 1);
}

// ---------- Parameter validation ----------

TEST(BioticKinetics, ParameterValidationPasses) {
    EXPECT_TRUE(KineticsValidation::validateParameters());
}

// ---------- Statistics ----------

TEST(BioticKinetics, StatsResetAndAccumulate) {
    KineticsStats::resetIteration();
    EXPECT_EQ(KineticsStats::iter_total_calls, 0);
    EXPECT_EQ(KineticsStats::iter_cells_with_biomass, 0);

    KineticsStats::accumulate(10.0, 1.0, 0.5, -0.3, false);
    EXPECT_EQ(KineticsStats::iter_total_calls, 1);
    EXPECT_EQ(KineticsStats::iter_cells_with_biomass, 1);
    EXPECT_EQ(KineticsStats::iter_cells_with_growth, 1);
}

// ---------- Mass balance ----------

TEST(BioticKinetics, MassBalanceYieldRelation) {
    // dDOC/dt should be ~ -mu * B / Y, and dB/dt ~ (mu - k_decay) * B
    // So |dDOC/dt| * Y ~ dB/dt + k_decay * B  (approximately)
    std::vector<double> B = {10.0};
    std::vector<double> C = {1.0};
    std::vector<double> subsR(2, 0.0), bioR(1, 0.0);
    defineRxnKinetics(B, C, subsR, bioR, 1);

    double doc_consumed = -subsR[0];
    double biomass_growth = bioR[0];
    // Expected: doc_consumed * Y = biomass_growth + k_decay * B[0]
    double expected_growth = doc_consumed * KineticParams::Y - KineticParams::k_decay * B[0];
    EXPECT_NEAR(biomass_growth, expected_growth, 1e-6);
}
