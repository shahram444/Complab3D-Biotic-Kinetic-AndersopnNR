// Extended unit tests for StabilityReport / performStabilityChecks
// Covers boundary conditions, edge cases, and combinations not in the base test file.

#include <gtest/gtest.h>
#include <cmath>
#include <limits>

typedef double T;

struct StabilityReport {
    T Ma, CFL, tau_NS, tau_ADE, Pe_grid;
    bool Ma_ok, Ma_warning, CFL_ok, tau_NS_ok, tau_ADE_ok, Pe_grid_ok, all_ok, has_warnings;
};

StabilityReport performStabilityChecks(T u_max, T tau_NS, T tau_ADE, T D_lattice) {
    StabilityReport report;
    T cs = std::sqrt(1.0 / 3.0);
    report.Ma = u_max / cs;
    report.Ma_ok = (report.Ma < 1.0);
    report.Ma_warning = (report.Ma > 0.3);
    report.CFL = u_max;
    report.CFL_ok = (report.CFL < 1.0);
    report.tau_NS = tau_NS;
    report.tau_NS_ok = (tau_NS > 0.5 && tau_NS < 2.0);
    report.tau_ADE = tau_ADE;
    report.tau_ADE_ok = (tau_ADE > 0.5 && tau_ADE < 2.0);
    report.Pe_grid = (D_lattice > 1e-14) ? (u_max / D_lattice) : 0.0;
    report.Pe_grid_ok = (report.Pe_grid < 2.0);
    report.all_ok = report.Ma_ok && report.CFL_ok && report.tau_NS_ok && report.tau_ADE_ok;
    report.has_warnings = report.Ma_warning || !report.Pe_grid_ok;
    return report;
}

// ============================================================================
// BOUNDARY VALUE TESTS
// ============================================================================

TEST(StabilityExtended, ExactMachThresholdOne) {
    // Ma exactly at 1.0 boundary (strict <)
    T cs = std::sqrt(1.0 / 3.0);
    T u_exact = cs;  // Ma = 1.0 exactly
    auto r = performStabilityChecks(u_exact, 0.8, 0.8, 0.1);
    EXPECT_FALSE(r.Ma_ok);  // Ma < 1.0 is false when Ma == 1.0
}

TEST(StabilityExtended, ExactMachWarningThreshold) {
    // Ma exactly at 0.3 boundary
    T cs = std::sqrt(1.0 / 3.0);
    T u_exact = 0.3 * cs;  // Ma = 0.3 exactly
    auto r = performStabilityChecks(u_exact, 0.8, 0.8, 0.1);
    EXPECT_TRUE(r.Ma_ok);
    EXPECT_FALSE(r.Ma_warning);  // Ma > 0.3 is false when exactly 0.3
}

TEST(StabilityExtended, ExactTauNSLowerBound) {
    // tau_NS = 0.5 exactly (strict >)
    auto r = performStabilityChecks(0.01, 0.5, 0.8, 0.1);
    EXPECT_FALSE(r.tau_NS_ok);  // 0.5 > 0.5 is false
}

TEST(StabilityExtended, ExactTauNSUpperBound) {
    // tau_NS = 2.0 exactly (strict <)
    auto r = performStabilityChecks(0.01, 2.0, 0.8, 0.1);
    EXPECT_FALSE(r.tau_NS_ok);  // 2.0 < 2.0 is false
}

TEST(StabilityExtended, ExactTauADEUpperBound) {
    auto r = performStabilityChecks(0.01, 0.8, 2.0, 0.1);
    EXPECT_FALSE(r.tau_ADE_ok);
}

TEST(StabilityExtended, ExactCFLOne) {
    auto r = performStabilityChecks(1.0, 0.8, 0.8, 0.5);
    EXPECT_FALSE(r.CFL_ok);
}

TEST(StabilityExtended, ExactPeGridTwo) {
    // Pe_grid = 2.0 exactly (strict <)
    auto r = performStabilityChecks(0.2, 0.8, 0.8, 0.1);
    EXPECT_FALSE(r.Pe_grid_ok);  // 2.0 < 2.0 is false
}

// ============================================================================
// ZERO AND NEAR-ZERO INPUTS
// ============================================================================

TEST(StabilityExtended, ZeroVelocity) {
    auto r = performStabilityChecks(0.0, 0.8, 0.8, 0.1);
    EXPECT_TRUE(r.Ma_ok);
    EXPECT_TRUE(r.CFL_ok);
    EXPECT_TRUE(r.Pe_grid_ok);
    EXPECT_TRUE(r.all_ok);
    EXPECT_DOUBLE_EQ(r.Ma, 0.0);
    EXPECT_DOUBLE_EQ(r.CFL, 0.0);
    EXPECT_DOUBLE_EQ(r.Pe_grid, 0.0);
}

TEST(StabilityExtended, VerySmallVelocity) {
    auto r = performStabilityChecks(1e-15, 0.8, 0.8, 0.1);
    EXPECT_TRUE(r.Ma_ok);
    EXPECT_TRUE(r.CFL_ok);
    EXPECT_TRUE(r.all_ok);
}

TEST(StabilityExtended, VerySmallDiffusion) {
    // D_lattice just above 1e-14 threshold
    auto r = performStabilityChecks(0.01, 0.8, 0.8, 1.01e-14);
    EXPECT_GT(r.Pe_grid, 0.0);
}

TEST(StabilityExtended, DiffusionAtThreshold) {
    auto r = performStabilityChecks(0.01, 0.8, 0.8, 1e-14);
    EXPECT_DOUBLE_EQ(r.Pe_grid, 0.0);  // At threshold, treated as zero
}

TEST(StabilityExtended, NegativeDiffusion) {
    auto r = performStabilityChecks(0.01, 0.8, 0.8, -0.1);
    EXPECT_DOUBLE_EQ(r.Pe_grid, 0.0);
}

// ============================================================================
// COMBINATION TESTS
// ============================================================================

TEST(StabilityExtended, AllFailures) {
    // Everything fails at once
    auto r = performStabilityChecks(2.0, 0.3, 0.3, 0.001);
    EXPECT_FALSE(r.Ma_ok);
    EXPECT_TRUE(r.Ma_warning);
    EXPECT_FALSE(r.CFL_ok);
    EXPECT_FALSE(r.tau_NS_ok);
    EXPECT_FALSE(r.tau_ADE_ok);
    EXPECT_FALSE(r.Pe_grid_ok);
    EXPECT_FALSE(r.all_ok);
    EXPECT_TRUE(r.has_warnings);
}

TEST(StabilityExtended, WarningsButNoFailures) {
    // Ma_warning but Ma_ok, and Pe_grid > 2 but everything else passes
    auto r = performStabilityChecks(0.2, 0.8, 0.8, 0.01);
    EXPECT_TRUE(r.Ma_ok);
    EXPECT_TRUE(r.Ma_warning);
    EXPECT_TRUE(r.CFL_ok);
    EXPECT_TRUE(r.tau_NS_ok);
    EXPECT_TRUE(r.tau_ADE_ok);
    EXPECT_TRUE(r.all_ok);
    EXPECT_TRUE(r.has_warnings);  // has_warnings includes Ma_warning OR !Pe_grid_ok
}

TEST(StabilityExtended, HasWarningsDueToMachOnly) {
    auto r = performStabilityChecks(0.2, 0.8, 0.8, 1.0);
    EXPECT_TRUE(r.has_warnings);   // Ma_warning is true
    EXPECT_TRUE(r.Pe_grid_ok);     // Pe_grid ok
}

TEST(StabilityExtended, HasWarningsDueToPeGridOnly) {
    auto r = performStabilityChecks(0.05, 0.8, 0.8, 0.01);
    EXPECT_FALSE(r.Ma_warning);  // Ma below 0.3
    EXPECT_FALSE(r.Pe_grid_ok);  // Pe_grid = 5.0
    EXPECT_TRUE(r.has_warnings);
}

// ============================================================================
// PHYSICAL SANITY TESTS
// ============================================================================

TEST(StabilityExtended, TypicalLBMParameters) {
    // Typical CompLaB3D simulation parameters
    T u_max = 0.01;  // typical lattice velocity
    T tau_NS = 0.8;
    T tau_ADE = 0.8;
    T D_lattice = (tau_ADE - 0.5) / 3.0;  // 0.1
    auto r = performStabilityChecks(u_max, tau_NS, tau_ADE, D_lattice);
    EXPECT_TRUE(r.all_ok);
    EXPECT_FALSE(r.has_warnings);
}

TEST(StabilityExtended, HighPecletSimulation) {
    // Pe = 100, need small tau_ADE
    T tau_ADE = 0.55;
    T D = (tau_ADE - 0.5) / 3.0;  // ~0.0167
    T u = 1.67;  // Pe_grid ~ 100 (bad!)
    auto r = performStabilityChecks(u, 0.8, tau_ADE, D);
    EXPECT_FALSE(r.Pe_grid_ok);
    EXPECT_FALSE(r.CFL_ok);
    EXPECT_TRUE(r.has_warnings);
}

TEST(StabilityExtended, TauNSJustAboveLowerBound) {
    auto r = performStabilityChecks(0.01, 0.500001, 0.8, 0.1);
    EXPECT_TRUE(r.tau_NS_ok);
}

TEST(StabilityExtended, TauNSJustBelowUpperBound) {
    auto r = performStabilityChecks(0.01, 1.999999, 0.8, 0.1);
    EXPECT_TRUE(r.tau_NS_ok);
}

// ============================================================================
// MACH NUMBER CALCULATION PRECISION
// ============================================================================

TEST(StabilityExtended, MachNumberPrecision) {
    T u_max = 0.1;
    auto r = performStabilityChecks(u_max, 0.8, 0.8, 0.1);
    T expected_Ma = u_max / std::sqrt(1.0 / 3.0);
    EXPECT_NEAR(r.Ma, expected_Ma, 1e-14);
}

TEST(StabilityExtended, PeGridPrecision) {
    T u_max = 0.05;
    T D = 0.1;
    auto r = performStabilityChecks(u_max, 0.8, 0.8, D);
    EXPECT_NEAR(r.Pe_grid, 0.5, 1e-14);
}
