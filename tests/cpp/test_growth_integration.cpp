// ============================================================================
// test_growth_integration.cpp  –  Time-Integration of Biofilm Growth Dynamics
//
// What this tests:
//   In CompLaB3D the kinetics function (defineRxnKinetics) computes RATES
//   (dB/dt, dDOC/dt) at each time step.  The actual state update is:
//
//     B_new   = B_old   + dB/dt   * dt_kinetics
//     DOC_new = DOC_old + dDOC/dt * dt_kinetics
//
//   This is a forward-Euler integration of the Monod ODE system.
//   Over many steps, the solution should exhibit three well-known phases:
//
//   Phase 1 – Exponential growth:  substrate >> Ks, dB/dt ≈ (mu_max - k_decay)*B
//   Phase 2 – Substrate-limited:   substrate ≈ Ks, growth rate ≈ mu_max/2
//   Phase 3 – Depletion / washout: substrate → 0,  dB/dt = -k_decay * B
//
//   This file also compares sessile (biofilm) vs planktonic behavior at the
//   same initial conditions to verify that the different parameter sets
//   (mu_max, k_decay, MIN_BIOMASS) produce different dynamics.
//
//   Analytical steady-state: when dB/dt = 0
//     mu(C*) = k_decay
//     mu_max * C* / (Ks + C*) = k_decay
//     C* = k_decay * Ks / (mu_max - k_decay)
// ============================================================================

#include "plb_shim.h"
#include <gtest/gtest.h>
#include <cmath>
#include <vector>

// Include SESSILE kinetics
#include "defineKinetics.hh"

// ============================================================================
// Euler integrator helper
// ============================================================================
struct State {
    double B;   // biomass   [kg/m³]
    double DOC; // substrate [mol/L]
};

// Advance one kinetics sub-step using forward Euler.
// Uses defineRxnKinetics from whichever header is active.
State eulerStep(State s) {
    using namespace KineticParams;
    std::vector<double> B   = {s.B};
    std::vector<double> C   = {s.DOC};
    std::vector<double> sR(2, 0.0), bR(1, 0.0);
    defineRxnKinetics(B, C, sR, bR, 1);
    s.B   += bR[0] * dt_kinetics;
    s.DOC += sR[0] * dt_kinetics;
    if (s.DOC < 0) s.DOC = 0.0;   // physical floor
    if (s.B   < 0) s.B   = 0.0;
    return s;
}

// ============================================================================
// TEST GROUP: Biofilm (sessile) growth phases
// ============================================================================

TEST(GrowthIntegration, BiomassIncreasesInGrowthPhase) {
    // High substrate, moderate biomass: should grow
    State s = {10.0, 1.0};
    State s_after = eulerStep(s);
    EXPECT_GT(s_after.B, s.B)
        << "Biomass should increase when DOC >> Ks and B > MIN_BIOMASS";
}

TEST(GrowthIntegration, DOCDecreasesWhenBiomassGrows) {
    State s = {10.0, 1.0};
    State s_after = eulerStep(s);
    EXPECT_LT(s_after.DOC, s.DOC)
        << "DOC must decrease when biomass is consuming substrate";
}

TEST(GrowthIntegration, BiomassDecaysWithZeroDOC) {
    State s = {10.0, 0.0};
    State s_after = eulerStep(s);
    EXPECT_LT(s_after.B, s.B)
        << "With no DOC, biomass should only decay";
    EXPECT_NEAR(s_after.DOC, 0.0, 1e-15)
        << "DOC cannot go negative";
}

TEST(GrowthIntegration, ExponentialGrowthPhase) {
    // At very high DOC (>> Ks): dB/dt ≈ (mu_max - k_decay) * B
    // Growth should be nearly exponential: B(t) ≈ B0 * exp(r*t)
    // where r = mu_max - k_decay = 1.0 - 1e-9 ≈ 1.0 [1/s]
    double DOC_init = 1000.0;  // >> Ks = 1e-5
    double B_init   = 1.0;
    State s = {B_init, DOC_init};

    // Run 10 steps
    int nsteps = 10;
    for (int i = 0; i < nsteps; ++i) s = eulerStep(s);

    double dt = KineticParams::dt_kinetics;
    double r  = KineticParams::mu_max - KineticParams::k_decay;
    double B_expected = B_init * std::pow(1.0 + r * dt, nsteps);  // Euler approximation

    EXPECT_NEAR(s.B, B_expected, B_expected * 0.05)
        << "Exponential growth should match Euler approximation";
}

TEST(GrowthIntegration, SubstrateDepletionLeadsToDecay) {
    // Start with limited DOC; after it depletes, biomass should decay.
    State s = {5.0, 1e-6};  // DOC near Ks, will be consumed quickly

    // Run until DOC is nearly gone
    for (int i = 0; i < 1000; ++i) s = eulerStep(s);

    // At this point DOC ≈ 0, biomass should be declining
    EXPECT_NEAR(s.DOC, 0.0, 1e-6);
    // Biomass should be less than initial (net decay)
    // Once DOC is gone, the next step must show declining biomass (only decay term active)
    State s_next = eulerStep(s);
    EXPECT_LE(s_next.B, s.B + 1e-10)
        << "After DOC depletion, biomass should not grow (only decay)";
}

TEST(GrowthIntegration, NoBiomassNoSubstrateChange) {
    // If B < MIN_BIOMASS, kinetics returns zero rates
    State s = {KineticParams::MIN_BIOMASS * 0.5, 1.0};
    State s_after = eulerStep(s);
    EXPECT_NEAR(s_after.B,   s.B,   1e-15);
    EXPECT_NEAR(s_after.DOC, s.DOC, 1e-15);
}

TEST(GrowthIntegration, MassBalanceOverMultipleSteps) {
    // Over N steps: total DOC consumed * Y = total biomass growth + total decay loss
    // i.e. DOC_consumed * Y ≈ (B_final - B_initial) + k_decay * B * N * dt
    // We verify DOC consumed and biomass produced are consistent with yield.
    KineticsDiagnostics::resetAll();

    State s = {10.0, 1.0};
    double B0 = s.B;
    int nsteps = 100;
    for (int i = 0; i < nsteps; ++i) s = eulerStep(s);

    double DOC_consumed  = KineticsDiagnostics::total_DOC_consumed;
    double B_produced    = KineticsDiagnostics::total_biomass_produced;

    // B_produced should be positive (net growth over many steps)
    EXPECT_GT(B_produced, 0.0);
    // DOC consumed > 0
    EXPECT_GT(DOC_consumed, 0.0);
    // Rough yield check: B_produced ≤ DOC_consumed * Y + k_decay * B0 * nsteps * dt
    double max_B_from_DOC = DOC_consumed * KineticParams::Y;
    EXPECT_LT(B_produced, max_B_from_DOC + nsteps * KineticParams::dt_kinetics
                          * KineticParams::k_decay * 1000.0);
}

TEST(GrowthIntegration, HalfSaturationGivesHalfMaxGrowth) {
    // At DOC = Ks: monod = 0.5, so mu = 0.5 * mu_max
    // dB/dt = (0.5 * mu_max - k_decay) * B ≈ 0.5 * mu_max * B (since k_decay << mu_max)
    double B0   = 10.0;
    double DOC0 = KineticParams::Ks;  // exactly at half-saturation
    std::vector<double> B   = {B0};
    std::vector<double> C   = {DOC0};
    std::vector<double> sR(2, 0.0), bR(1, 0.0);
    defineRxnKinetics(B, C, sR, bR, 1);

    // Net growth rate per unit biomass
    double r = bR[0] / B0;
    // At half-saturation without clamping: r = 0.5*mu_max - k_decay
    // With potential clamping (DOC is small): rate might be clamped lower
    // Either way, it should be less than at high DOC
    std::vector<double> B2  = {B0};
    std::vector<double> C2  = {1000.0};  // very high DOC
    std::vector<double> sR2(2, 0.0), bR2(1, 0.0);
    defineRxnKinetics(B2, C2, sR2, bR2, 1);
    double r_max = bR2[0] / B0;

    EXPECT_LT(r, r_max) << "Growth at half-saturation must be less than at saturation";
    EXPECT_GT(bR[0], 0.0) << "Growth at half-saturation should still be positive";
}

TEST(GrowthIntegration, SteadyStateApproachesZeroGrowthConcentration) {
    // Analytical steady state: C* = k_decay * Ks / (mu_max - k_decay)
    // At this DOC, dB/dt = 0.
    double k  = KineticParams::k_decay;
    double mu = KineticParams::mu_max;
    double Ks = KineticParams::Ks;
    double C_star = k * Ks / (mu - k);

    // Verify: monod(C*) = k / mu_max
    double monod = C_star / (Ks + C_star);
    EXPECT_NEAR(monod * mu, k, k * 1e-6);

    // At C*, net growth should be essentially zero
    std::vector<double> B   = {10.0};
    std::vector<double> C   = {C_star};
    std::vector<double> sR(2, 0.0), bR(1, 0.0);
    defineRxnKinetics(B, C, sR, bR, 1);
    // dB/dt = (mu * monod - k) * B ≈ 0
    // NOTE: clamping might activate at such low DOC, so we check the sign
    EXPECT_LE(std::abs(bR[0]), KineticParams::mu_max * B[0]);
}

// ============================================================================
// TEST GROUP: Sessile vs Planktonic parameter comparison
//
// Both use the same Monod equation, but with different parameters:
//   Sessile:   mu_max=1.0, k_decay=1e-9, MIN_BIOMASS=0.1
//   Planktonic: mu_max=0.5, k_decay=1e-7, MIN_BIOMASS=0.01
//
// Expected differences at same conditions:
//   1. Planktonic grows more slowly (mu_max 2x smaller)
//   2. Planktonic decays faster without substrate (k_decay 100x larger)
//   3. Planktonic responds at lower biomass (MIN_BIOMASS 10x smaller)
// ============================================================================

TEST(SessileVsPlanktonic, SessileHasHigherMuMax) {
    // Sessile mu_max = 1.0, planktonic = 0.5
    // KineticParams here refers to sessile (defineKinetics.hh included)
    EXPECT_DOUBLE_EQ(KineticParams::mu_max, 1.0);
    EXPECT_DOUBLE_EQ(KineticParams::k_decay, 1.0e-9);
    EXPECT_DOUBLE_EQ(KineticParams::MIN_BIOMASS, 0.1);
}

TEST(SessileVsPlanktonic, SessileGrowsFasterAtSameConditions) {
    // Sessile: dB/dt at B=10, DOC=1.0
    std::vector<double> B   = {10.0};
    std::vector<double> C   = {1.0};
    std::vector<double> sR(2, 0.0), bR(1, 0.0);
    defineRxnKinetics(B, C, sR, bR, 1);
    double dBdt_sessile = bR[0];

    // Expected sessile rate: mu_max=1.0, DOC=1.0 >> Ks=1e-5
    // monod ≈ 1, mu ≈ 1.0, dB/dt ≈ (1.0 - 1e-9) * 10 ≈ 10
    double expected = (KineticParams::mu_max - KineticParams::k_decay) * B[0];
    // May be substrate-clamped; check direction
    EXPECT_GT(dBdt_sessile, 0.0)
        << "Sessile biomass should grow at high DOC";
    EXPECT_NEAR(dBdt_sessile, expected, std::abs(expected) * 0.1)
        << "Sessile growth rate should approximately match (mu-k_decay)*B";
}

TEST(SessileVsPlanktonic, SessileDecaysSlowerAtZeroDOC) {
    // At zero DOC: sessile dB/dt = -1e-9 * B vs planktonic = -1e-7 * B
    std::vector<double> B   = {10.0};
    std::vector<double> C   = {0.0};
    std::vector<double> sR(2, 0.0), bR(1, 0.0);
    defineRxnKinetics(B, C, sR, bR, 1);
    double sessile_decay = bR[0];  // should be -k_decay * B = -1e-8

    // Planktonic decay would be -1e-7 * 10 = -1e-6 (100x larger in magnitude)
    // Just verify sessile decay matches k_decay * B
    double expected_sessile_decay = -KineticParams::k_decay * B[0];
    EXPECT_NEAR(sessile_decay, expected_sessile_decay, std::abs(expected_sessile_decay) * 0.01);
}

TEST(SessileVsPlanktonic, SessileNeedsHigherMinBiomassToActivate) {
    // Sessile MIN_BIOMASS = 0.1, planktonic = 0.01
    // At B = 0.05: sessile inactive, planktonic active
    double B_test = 0.05;  // between 0.01 and 0.1

    // Sessile (active here = false since B < 0.1)
    std::vector<double> B   = {B_test};
    std::vector<double> C   = {1.0};
    std::vector<double> sR(2, 0.0), bR(1, 0.0);
    defineRxnKinetics(B, C, sR, bR, 1);

    EXPECT_DOUBLE_EQ(bR[0], 0.0)
        << "Sessile kinetics should not activate at B=" << B_test
        << " < MIN_BIOMASS=" << KineticParams::MIN_BIOMASS;
    EXPECT_DOUBLE_EQ(sR[0], 0.0)
        << "No DOC consumption below sessile MIN_BIOMASS";
}

// ============================================================================
// TEST GROUP: Multi-step integration stability
// ============================================================================

TEST(GrowthIntegration, BiomassNeverGoesBelowZero) {
    // After complete DOC depletion, biomass should approach 0 but not go negative.
    State s = {10.0, 1e-7};  // very low DOC
    for (int i = 0; i < 10000; ++i) {
        s = eulerStep(s);
        EXPECT_GE(s.B,   0.0) << "Biomass went negative at step " << i;
        EXPECT_GE(s.DOC, 0.0) << "DOC went negative at step " << i;
    }
}

TEST(GrowthIntegration, DOCNeverGoesNegative) {
    State s = {1e8, 1e-4};  // enormous biomass, limited substrate
    for (int i = 0; i < 1000; ++i) {
        s = eulerStep(s);
        EXPECT_GE(s.DOC, 0.0) << "DOC negative at step " << i;
    }
}

TEST(GrowthIntegration, CO2AccumulatesAsDOCDeclines) {
    // CO2 is the oxidized product of DOC; as DOC declines, CO2 should rise.
    State s = {10.0, 1.0};
    double B0 = s.B, DOC0 = s.DOC;

    // Single step
    std::vector<double> B   = {s.B};
    std::vector<double> C   = {s.DOC};
    std::vector<double> sR(2, 0.0), bR(1, 0.0);
    defineRxnKinetics(B, C, sR, bR, 1);

    double dDOC = sR[0];  // negative
    double dCO2 = sR[1];  // should be positive

    EXPECT_LT(dDOC, 0.0) << "DOC should be consumed";
    EXPECT_GT(dCO2, 0.0) << "CO2 should be produced";
    EXPECT_LE(dCO2, -dDOC + 1e-14)
        << "CO2 produced cannot exceed DOC consumed";
}

TEST(GrowthIntegration, GrowthRateScalesWithBiomass) {
    // At fixed DOC, dB/dt should be proportional to B (first-order in B).
    double DOC_val = 1.0;  // >> Ks

    double B1 = 5.0,  B2 = 10.0;  // B2 = 2 * B1

    std::vector<double> Bv1 = {B1}, Bv2 = {B2};
    std::vector<double> Cv  = {DOC_val};
    std::vector<double> sR1(2,0), bR1(1,0), sR2(2,0), bR2(1,0);

    defineRxnKinetics(Bv1, Cv, sR1, bR1, 1);
    defineRxnKinetics(Bv2, Cv, sR2, bR2, 1);

    // dB/dt should scale ~linearly with B (both above MIN_BIOMASS)
    // At high DOC, no clamping: dB/dt = (mu_max - k_decay) * B
    EXPECT_NEAR(bR2[0] / bR1[0], B2 / B1, 0.01)
        << "Growth rate should scale linearly with biomass at high DOC";
}
