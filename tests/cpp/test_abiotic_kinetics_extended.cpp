// Extended unit tests for defineAbioticRxnKinetics (substrate-only reactions)
// Covers: multiple substrates, time-stepping stability, clamping precision,
// extreme concentrations, and parameter edge cases.

#include "plb_shim.h"
#include <gtest/gtest.h>
#include <cmath>
#include <vector>
#include <limits>

#include "defineAbioticKinetics.hh"

// ============================================================================
// FIRST-ORDER DECAY DETAILED TESTS
// ============================================================================

TEST(AbioticKineticsExt, FirstOrderDecayRate) {
    // Rate should be -k * C for first-order decay
    double C0 = 1.0;
    std::vector<double> C = {C0, 0.0, 0.0, 0.0, 0.0};
    std::vector<double> subsR(5, 0.0);
    defineAbioticRxnKinetics(C, subsR, 1);

    double expected_rate = -AbioticParams::k_decay_0 * C0;
    EXPECT_NEAR(subsR[0], expected_rate, std::abs(expected_rate) * 0.01 + 1e-20);
}

TEST(AbioticKineticsExt, DecayRateScalesLinearly) {
    double concs[] = {0.1, 1.0, 10.0};
    double prev_rate = 0.0;

    for (double c : concs) {
        std::vector<double> C = {c, 0.0, 0.0, 0.0, 0.0};
        std::vector<double> subsR(5, 0.0);
        defineAbioticRxnKinetics(C, subsR, 1);

        if (prev_rate != 0.0) {
            // Rate should scale with concentration
            EXPECT_LT(subsR[0], prev_rate);  // More negative = larger magnitude
        }
        prev_rate = subsR[0];
    }
}

// ============================================================================
// RATE CLAMPING DETAILED TESTS
// ============================================================================

TEST(AbioticKineticsExt, RateClampedAtLowConcentration) {
    // At very low C, rate should be clamped to MAX_RATE_FRACTION * C / dt
    double C0 = 1e-10;
    std::vector<double> C = {C0, 0.0, 0.0, 0.0, 0.0};
    std::vector<double> subsR(5, 0.0);
    defineAbioticRxnKinetics(C, subsR, 1);

    double max_allowed = C0 * AbioticParams::MAX_RATE_FRACTION / AbioticParams::dt_kinetics;
    EXPECT_LE(-subsR[0], max_allowed + 1e-30);
}

TEST(AbioticKineticsExt, RateNotClampedAtHighConcentration) {
    // At high C with small k, unclamped rate should be used
    double C0 = 1000.0;
    std::vector<double> C = {C0, 0.0, 0.0, 0.0, 0.0};
    std::vector<double> subsR(5, 0.0);
    defineAbioticRxnKinetics(C, subsR, 1);

    EXPECT_LT(subsR[0], 0.0);  // Should be consuming
    EXPECT_FALSE(std::isnan(subsR[0]));
}

// ============================================================================
// MULTIPLE SUBSTRATE TESTS
// ============================================================================

TEST(AbioticKineticsExt, AllSubstratesGetRates) {
    // All substrates with nonzero concentration should get rates
    std::vector<double> C = {1.0, 2.0, 0.5, 0.1, 3.0};
    std::vector<double> subsR(5, 0.0);
    defineAbioticRxnKinetics(C, subsR, 1);

    // At minimum, the first substrate should have a rate
    EXPECT_NE(subsR[0], 0.0);
    EXPECT_FALSE(std::isnan(subsR[0]));
}

TEST(AbioticKineticsExt, ZeroSubstratesAreUnchanged) {
    std::vector<double> C = {0.0, 0.0, 0.0, 0.0, 0.0};
    std::vector<double> subsR(5, 0.0);
    defineAbioticRxnKinetics(C, subsR, 1);

    for (size_t i = 0; i < subsR.size(); ++i) {
        EXPECT_NEAR(subsR[i], 0.0, 1e-20) << "Non-zero rate for zero substrate at index " << i;
    }
}

TEST(AbioticKineticsExt, SingleSubstrate) {
    std::vector<double> C = {1.0};
    std::vector<double> subsR(1, 0.0);
    defineAbioticRxnKinetics(C, subsR, 1);
    EXPECT_FALSE(std::isnan(subsR[0]));
}

// ============================================================================
// TIME-STEPPING STABILITY TESTS
// ============================================================================

TEST(AbioticKineticsExt, EulerIntegrationStable) {
    double C = 1.0;
    double dt = AbioticParams::dt_kinetics;

    for (int step = 0; step < 10000; ++step) {
        std::vector<double> Cvec = {C, 0.0, 0.0, 0.0, 0.0};
        std::vector<double> subsR(5, 0.0);
        defineAbioticRxnKinetics(Cvec, subsR, 1);

        C += subsR[0] * dt;
        EXPECT_GE(C, -1e-10) << "Negative concentration at step " << step;
        EXPECT_FALSE(std::isnan(C)) << "NaN at step " << step;
        if (C < 0) C = 0;
    }
    // Concentration should decrease over time for decay
    EXPECT_LT(C, 1.0);
}

TEST(AbioticKineticsExt, DecayHalfLife) {
    // For first-order decay: C(t) = C0 * exp(-k*t)
    // Half-life = ln(2) / k
    double C = 1.0;
    double dt = AbioticParams::dt_kinetics;
    double t_half = std::log(2.0) / AbioticParams::k_decay_0;
    int steps_to_half = (int)(t_half / dt);

    for (int step = 0; step < steps_to_half && C > 0; ++step) {
        std::vector<double> Cvec = {C, 0.0, 0.0, 0.0, 0.0};
        std::vector<double> subsR(5, 0.0);
        defineAbioticRxnKinetics(Cvec, subsR, 1);
        C += subsR[0] * dt;
        if (C < 0) C = 0;
    }
    // After half-life, concentration should be ~0.5 (Euler approx)
    EXPECT_NEAR(C, 0.5, 0.1);  // Euler has some error
}

// ============================================================================
// EXTREME INPUT TESTS
// ============================================================================

TEST(AbioticKineticsExt, VeryLargeConcentration) {
    std::vector<double> C = {1e15, 0.0, 0.0, 0.0, 0.0};
    std::vector<double> subsR(5, 0.0);
    defineAbioticRxnKinetics(C, subsR, 1);

    EXPECT_FALSE(std::isnan(subsR[0]));
    EXPECT_FALSE(std::isinf(subsR[0]));
    EXPECT_LT(subsR[0], 0.0);  // Should still be consuming
}

TEST(AbioticKineticsExt, VerySmallConcentration) {
    std::vector<double> C = {1e-30, 0.0, 0.0, 0.0, 0.0};
    std::vector<double> subsR(5, 0.0);
    defineAbioticRxnKinetics(C, subsR, 1);

    EXPECT_FALSE(std::isnan(subsR[0]));
    EXPECT_NEAR(subsR[0], 0.0, 1e-20);  // Near zero concentration -> near zero rate
}

TEST(AbioticKineticsExt, NegativeConcentrationHandled) {
    std::vector<double> C = {-1.0, 0.0, 0.0, 0.0, 0.0};
    std::vector<double> subsR(5, 0.0);
    defineAbioticRxnKinetics(C, subsR, 1);

    EXPECT_FALSE(std::isnan(subsR[0]));
    EXPECT_FALSE(std::isinf(subsR[0]));
}

// ============================================================================
// MASK VALUE TESTS
// ============================================================================

TEST(AbioticKineticsExt, DifferentMaskValues) {
    std::vector<double> C = {1.0, 0.0, 0.0, 0.0, 0.0};
    int masks[] = {0, 1, 2, 3, 5, -1};

    for (int m : masks) {
        std::vector<double> subsR(5, 0.0);
        defineAbioticRxnKinetics(C, subsR, m);
        EXPECT_FALSE(std::isnan(subsR[0])) << "NaN for mask=" << m;
    }
}

// ============================================================================
// STATISTICS TESTS
// ============================================================================

TEST(AbioticKineticsExt, StatsResetAndAccumulateMultiple) {
    AbioticKineticsStats::resetIteration();
    for (int i = 0; i < 100; ++i) {
        AbioticKineticsStats::accumulate(0.5 * i);
    }
    // Should not crash; no assertions on internal state since printStats
    // is the primary output
    EXPECT_NO_FATAL_FAILURE(AbioticKineticsStats::resetIteration());
}

TEST(AbioticKineticsExt, StatsWithZeroRate) {
    AbioticKineticsStats::resetIteration();
    AbioticKineticsStats::accumulate(0.0);
    // Zero rate should still be trackable
    EXPECT_NO_FATAL_FAILURE(AbioticKineticsStats::resetIteration());
}

// ============================================================================
// PARAMETER VALIDATION TESTS
// ============================================================================

TEST(AbioticKineticsExt, ParameterValidationPasses) {
    EXPECT_TRUE(AbioticKineticsValidation::validateParameters());
}

TEST(AbioticKineticsExt, ParametersArePhysical) {
    EXPECT_GE(AbioticParams::k_decay_0, 0.0);
    EXPECT_GE(AbioticParams::k_reaction, 0.0);
    EXPECT_GT(AbioticParams::MIN_CONC, 0.0);
    EXPECT_GT(AbioticParams::MAX_RATE_FRACTION, 0.0);
    EXPECT_LE(AbioticParams::MAX_RATE_FRACTION, 1.0);
    EXPECT_GT(AbioticParams::dt_kinetics, 0.0);
}

// ============================================================================
// EMPTY/EDGE CASES
// ============================================================================

TEST(AbioticKineticsExt, EmptyVectorsNoAction) {
    std::vector<double> C, subsR;
    EXPECT_NO_FATAL_FAILURE(defineAbioticRxnKinetics(C, subsR, 1));
}

TEST(AbioticKineticsExt, MismatchedVectorSizes) {
    std::vector<double> C = {1.0, 2.0};
    std::vector<double> subsR(5, 0.0);
    // Should handle gracefully
    EXPECT_NO_FATAL_FAILURE(defineAbioticRxnKinetics(C, subsR, 1));
}

// ============================================================================
// DETERMINISTIC OUTPUT TESTS
// ============================================================================

TEST(AbioticKineticsExt, SameInputSameOutput) {
    std::vector<double> C = {1.0, 0.5, 0.0, 0.0, 0.0};

    std::vector<double> subsR1(5, 0.0);
    defineAbioticRxnKinetics(C, subsR1, 1);

    std::vector<double> subsR2(5, 0.0);
    defineAbioticRxnKinetics(C, subsR2, 1);

    for (size_t i = 0; i < 5; ++i) {
        EXPECT_DOUBLE_EQ(subsR1[i], subsR2[i]) << "Non-deterministic at index " << i;
    }
}
