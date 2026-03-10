// Unit tests for StabilityReport / performStabilityChecks
// These functions are defined in src/complab.cpp; we replicate the struct and
// function here so the tests can build without the full Palabos dependency.

#include <gtest/gtest.h>
#include <cmath>

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

// ---------- Mach number tests ----------

TEST(StabilityChecks, LowMachIsOk) {
    auto r = performStabilityChecks(0.01, 0.8, 0.8, 0.1);
    EXPECT_TRUE(r.Ma_ok);
    EXPECT_FALSE(r.Ma_warning);
    EXPECT_NEAR(r.Ma, 0.01 / std::sqrt(1.0 / 3.0), 1e-10);
}

TEST(StabilityChecks, HighMachNotOk) {
    auto r = performStabilityChecks(0.7, 0.8, 0.8, 0.1);
    EXPECT_FALSE(r.Ma_ok);      // Ma > 1
    EXPECT_TRUE(r.Ma_warning);  // Ma > 0.3
}

TEST(StabilityChecks, MachWarningRange) {
    // Ma between 0.3 and 1.0
    auto r = performStabilityChecks(0.2, 0.8, 0.8, 0.1);
    EXPECT_TRUE(r.Ma_ok);
    EXPECT_TRUE(r.Ma_warning);
}

// ---------- CFL tests ----------

TEST(StabilityChecks, CflBelowOne) {
    auto r = performStabilityChecks(0.5, 0.8, 0.8, 1.0);
    EXPECT_TRUE(r.CFL_ok);
    EXPECT_DOUBLE_EQ(r.CFL, 0.5);
}

TEST(StabilityChecks, CflAboveOne) {
    auto r = performStabilityChecks(1.5, 0.8, 0.8, 1.0);
    EXPECT_FALSE(r.CFL_ok);
}

// ---------- Relaxation time tests ----------

TEST(StabilityChecks, ValidTauNS) {
    auto r = performStabilityChecks(0.01, 0.8, 0.8, 0.1);
    EXPECT_TRUE(r.tau_NS_ok);
}

TEST(StabilityChecks, TauNSTooLow) {
    auto r = performStabilityChecks(0.01, 0.4, 0.8, 0.1);
    EXPECT_FALSE(r.tau_NS_ok);
    EXPECT_FALSE(r.all_ok);
}

TEST(StabilityChecks, TauNSTooHigh) {
    auto r = performStabilityChecks(0.01, 2.5, 0.8, 0.1);
    EXPECT_FALSE(r.tau_NS_ok);
}

TEST(StabilityChecks, TauADETooLow) {
    auto r = performStabilityChecks(0.01, 0.8, 0.3, 0.1);
    EXPECT_FALSE(r.tau_ADE_ok);
    EXPECT_FALSE(r.all_ok);
}

// ---------- Grid Peclet tests ----------

TEST(StabilityChecks, PeGridBelowTwo) {
    auto r = performStabilityChecks(0.01, 0.8, 0.8, 0.1);
    EXPECT_DOUBLE_EQ(r.Pe_grid, 0.01 / 0.1);
    EXPECT_TRUE(r.Pe_grid_ok);
}

TEST(StabilityChecks, PeGridAboveTwo) {
    auto r = performStabilityChecks(0.5, 0.8, 0.8, 0.1);
    EXPECT_FALSE(r.Pe_grid_ok);
    EXPECT_TRUE(r.has_warnings);
}

TEST(StabilityChecks, ZeroDiffusionGivesPeZero) {
    auto r = performStabilityChecks(0.01, 0.8, 0.8, 0.0);
    EXPECT_DOUBLE_EQ(r.Pe_grid, 0.0);
    EXPECT_TRUE(r.Pe_grid_ok);
}

// ---------- Composite flag tests ----------

TEST(StabilityChecks, AllOkWhenEverythingGood) {
    auto r = performStabilityChecks(0.01, 0.8, 0.8, 0.1);
    EXPECT_TRUE(r.all_ok);
}

TEST(StabilityChecks, AllNotOkWithBadTau) {
    auto r = performStabilityChecks(0.01, 0.4, 0.3, 0.1);
    EXPECT_FALSE(r.all_ok);
}
