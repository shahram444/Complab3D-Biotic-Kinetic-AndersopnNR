// Unit tests for defineAbioticRxnKinetics (abiotic kinetics functions)
// Uses a minimal plb shim so the header can compile without Palabos.

#include "plb_shim.h"
#include <gtest/gtest.h>

// Include the production header (from project root)
#include "defineAbioticKinetics.hh"

// ---------- Basic rate computation ----------

TEST(AbioticKinetics, ZeroConcentrationGivesNearZeroRate) {
    std::vector<double> C = {0.0};
    std::vector<double> subsR(1, 0.0);
    defineAbioticRxnKinetics(C, subsR, /*mask=*/1);
    // With zero concentration the rate should be negligible (MIN_CONC is used)
    EXPECT_LE(std::abs(subsR[0]), 1e-15);
}

TEST(AbioticKinetics, PositiveConcentrationGivesNegativeRate) {
    std::vector<double> C = {1.0};  // 1 mol/L
    std::vector<double> subsR(1, 0.0);
    defineAbioticRxnKinetics(C, subsR, 1);
    // First-order decay: rate should be negative (consumption)
    EXPECT_LT(subsR[0], 0.0);
}

TEST(AbioticKinetics, RateProportionalToConcentration) {
    std::vector<double> C1 = {1.0};
    std::vector<double> C2 = {2.0};
    std::vector<double> R1(1, 0.0), R2(1, 0.0);

    defineAbioticRxnKinetics(C1, R1, 1);
    defineAbioticRxnKinetics(C2, R2, 1);

    // First-order: doubling concentration should roughly double the rate
    EXPECT_NEAR(R2[0] / R1[0], 2.0, 0.01);
}

// ---------- Output sanity ----------

TEST(AbioticKinetics, NoNanOrInfInOutput) {
    std::vector<double> C = {1.0e-5};
    std::vector<double> subsR(1, 0.0);
    defineAbioticRxnKinetics(C, subsR, 1);
    EXPECT_FALSE(std::isnan(subsR[0]));
    EXPECT_FALSE(std::isinf(subsR[0]));
}

TEST(AbioticKinetics, MultipleSubstratesInitializedToZero) {
    // When we pass 3 substrates, only substrate 0 should have a nonzero rate
    // (the default implementation only handles substrate 0; bimolecular is
    // commented out).
    std::vector<double> C = {1.0, 0.5, 0.0};
    std::vector<double> subsR(3, 999.0);  // deliberately non-zero sentinel
    defineAbioticRxnKinetics(C, subsR, 1);
    EXPECT_LT(subsR[0], 0.0);       // substrate 0 decays
    EXPECT_DOUBLE_EQ(subsR[1], 0.0); // others untouched
    EXPECT_DOUBLE_EQ(subsR[2], 0.0);
}

// ---------- Rate clamping ----------

TEST(AbioticKinetics, RateClampedToFractionOfConcentration) {
    // Very high rate constant would otherwise consume more than exists;
    // the MAX_RATE_FRACTION clamp should prevent that.
    // With default k_decay_0 = 1e-5, moderate concentrations won't trigger
    // the clamp.  We test with the existing parameters to verify the result
    // stays within the allowed envelope.
    double conc = 1.0e-3;
    std::vector<double> C = {conc};
    std::vector<double> subsR(1, 0.0);
    defineAbioticRxnKinetics(C, subsR, 1);

    double max_allowed = conc * AbioticParams::MAX_RATE_FRACTION / AbioticParams::dt_kinetics;
    EXPECT_LE(-subsR[0], max_allowed + 1e-30);
}

// ---------- Parameter validation ----------

TEST(AbioticKinetics, ParameterValidationPasses) {
    EXPECT_TRUE(AbioticKineticsValidation::validateParameters());
}

// ---------- Statistics accumulator ----------

TEST(AbioticKinetics, StatsAccumulateCorrectly) {
    AbioticKineticsStats::resetIteration();
    AbioticKineticsStats::accumulate(0.0);   // zero rate -> not reacting
    AbioticKineticsStats::accumulate(-1e-3); // non-zero -> reacting

    EXPECT_EQ(AbioticKineticsStats::iter_total_calls, 2);
    EXPECT_EQ(AbioticKineticsStats::iter_cells_reacting, 1);
}
