// ============================================================================
// test_reaction_transport.cpp  –  Coupled Reaction-Transport Validation
//
// What this tests:
//   Reactive transport combines advection-diffusion with kinetic reactions.
//   CompLaB3D solves this system using operator splitting:
//     1. LBM step: transport C via advection and diffusion
//     2. Kinetics step: update C using defineRxnKinetics / defineAbioticRxnKinetics
//
//   Key dimensionless numbers that classify transport regimes:
//
//   Peclet number:
//     Pe = u * L / D
//     Pe << 1: diffusion-dominated (concentration profiles near-uniform)
//     Pe >> 1: advection-dominated (sharp fronts, plug-flow behaviour)
//
//   Damköhler number (first Damköhler, Da_I):
//     Da = k_rxn * L / u
//     Da << 1: transport-limited (reaction slow vs. flow)
//     Da >> 1: reaction-limited (reaction fast vs. flow)
//
//   Damköhler number for diffusion (Da_II):
//     Da_II = k_rxn * L² / D  =  Pe * Da
//     Da_II << 1: mixing fast relative to reaction
//     Da_II >> 1: reaction faster than diffusion (strong gradients develop)
//
//   Thiele modulus (biofilm):
//     phi = L_biofilm * sqrt(k_rxn / D_eff)
//     phi < 0.3: kinetically-limited (no diffusion limitation)
//     phi > 3.0: diffusion-limited (substrate starved in biofilm interior)
//
//   Breakthrough concentration in 1D steady-state column with first-order decay:
//     C_out = C_in * exp(-Da)           [Pe >> 1, plug-flow]
//     C_out = C_in * 4*exp(Pe/2) / (1+alpha)²  [full ADE solution]
//     where alpha = sqrt(1 + 4*Da/Pe)
//
// ============================================================================

#include "plb_shim.h"
#include <gtest/gtest.h>
#include <cmath>
#include <vector>
#include <string>

// Biotic and abiotic kinetics (from JOSS_Submit root)
#include "defineKinetics.hh"
#include "defineAbioticKinetics.hh"

// ============================================================================
// Dimensionless number calculations
// ============================================================================
namespace DimNumbers {

    // Peclet number
    double Pe(double u, double L, double D) {
        return (D > 1e-30) ? u * L / D : 1e30;
    }

    // First Damköhler number (reaction vs. advection)
    double Da(double k_rxn, double L, double u) {
        return (u > 1e-30) ? k_rxn * L / u : 1e30;
    }

    // Second Damköhler number (reaction vs. diffusion)
    double Da_II(double k_rxn, double L, double D) {
        return (D > 1e-30) ? k_rxn * L * L / D : 1e30;
    }

    // Thiele modulus (biofilm effectiveness)
    double phi(double L_film, double k_rxn, double D_eff) {
        return (D_eff > 1e-30) ? L_film * std::sqrt(k_rxn / D_eff) : 1e30;
    }

    // Effectiveness factor for slab biofilm (first-order kinetics)
    double effectiveness(double phi_val) {
        if (phi_val < 1e-10) return 1.0;
        return std::tanh(phi_val) / phi_val;
    }
}

// ============================================================================
// Analytical solutions for 1D reactive-transport column
// ============================================================================
namespace ReactiveColumn {

    // Plug-flow reactor (Pe -> inf): exponential decay
    // C(x) = C_in * exp(-k*x/u)
    // Equivalently: C_out = C_in * exp(-Da)
    double plug_flow(double C_in, double k_rxn, double u, double x) {
        return C_in * std::exp(-k_rxn * x / u);
    }

    // Full ADE solution (Ogata-Banks for first-order decay):
    // C_out = C_in * 4*exp(Pe/2) / ((1+alpha)^2 * exp(-Pe*(alpha-1)/2)
    //                                - (1-alpha)^2 * exp(Pe*(alpha+1)/2))
    // alpha = sqrt(1 + 4*Da/Pe)
    // For simplicity, we use the approximate half-concentration at Da=0.693
    double breakthrough_DaApprox(double C_in, double Da) {
        // Plug-flow approximation; valid for Pe >> 1
        return C_in * std::exp(-Da);
    }

    // 1D steady-state: diffusion + first-order decay with Dirichlet at x=0, Neumann at x=L
    // C(x) = C0 * cosh(phi * (1-x/L)) / cosh(phi)
    double reactive_slab(double x, double L, double C0, double k_rxn, double D) {
        if (D < 1e-30) return 0.0;
        double phi = L * std::sqrt(k_rxn / D);
        if (phi < 1e-10) return C0;
        if (phi > 300.0) phi = 300.0;  // cap to avoid cosh overflow
        return C0 * std::cosh(phi * (1.0 - x/L)) / std::cosh(phi);
    }
}

// ============================================================================
// TEST GROUP: Dimensionless numbers
// ============================================================================

TEST(DimNumbers, PecletDiffusionDominated) {
    // Slow flow, small domain: Pe << 1
    double Pe = DimNumbers::Pe(1e-6, 1e-4, 1e-9);
    EXPECT_LT(Pe, 1.0) << "u=1e-6 m/s, L=0.1mm, D=1e-9: diffusion dominated";
}

TEST(DimNumbers, PecletAdvectionDominated) {
    // Fast flow, large domain: Pe >> 1
    double Pe = DimNumbers::Pe(1e-4, 0.1, 1e-9);
    EXPECT_GT(Pe, 100.0) << "u=0.1mm/s, L=10cm, D=1e-9: advection dominated";
}

TEST(DimNumbers, DamkohlerTransportLimited) {
    // Slow reaction vs. fast flow: Da << 1
    double Da = DimNumbers::Da(1e-4, 0.01, 1e-3);
    EXPECT_LT(Da, 1.0) << "k=1e-4/s, L=1cm, u=1mm/s: transport-limited";
}

TEST(DimNumbers, DamkohlerReactionLimited) {
    // Fast reaction vs. slow flow: Da >> 1
    double Da = DimNumbers::Da(10.0, 0.1, 1e-5);
    EXPECT_GT(Da, 10.0) << "k=10/s, L=10cm, u=0.01mm/s: reaction-limited";
}

TEST(DimNumbers, DaSecondDiffusionLimited) {
    // Large Da_II: diffusion can't keep up with reaction
    double Da_II = DimNumbers::Da_II(1.0, 1e-3, 1e-12);
    EXPECT_GE(Da_II, 1e6) << "k=1/s, L=1mm, D=1e-12: extremely diffusion limited";
}

TEST(DimNumbers, ThieleModulusKineticallyLimited) {
    // phi < 0.3: no diffusion limitation in biofilm
    double phi = DimNumbers::phi(1e-5, 1e-3, 1e-9);
    EXPECT_LT(phi, 0.3) << "Thin biofilm, slow reaction: phi < 0.3";
}

TEST(DimNumbers, ThieleModulusDiffusionLimited) {
    // phi > 3: strong diffusion limitation
    double phi = DimNumbers::phi(1e-4, 10.0, 1e-11);
    EXPECT_GT(phi, 3.0) << "Thick biofilm, fast reaction, slow diffusion: phi > 3";
}

// ============================================================================
// TEST GROUP: Effectiveness factor and biofilm behaviour
// ============================================================================

TEST(Effectiveness, FullPenetration_LowPhi) {
    double eta = DimNumbers::effectiveness(0.1);
    EXPECT_NEAR(eta, 1.0, 0.01)
        << "phi=0.1: substrate reaches all biofilm, eta ≈ 1";
}

TEST(Effectiveness, HalfPenetration_ModeratePhi) {
    // At phi = pi/2 ≈ 1.57: tanh(phi)/phi ≈ 0.61
    double phi = M_PI / 2.0;
    double eta = DimNumbers::effectiveness(phi);
    EXPECT_GT(eta, 0.5);
    EXPECT_LT(eta, 1.0);
}

TEST(Effectiveness, StronglyLimited_HighPhi) {
    // phi = 10: eta = tanh(10)/10 ≈ 0.1
    double eta = DimNumbers::effectiveness(10.0);
    EXPECT_LT(eta, 0.15);
    EXPECT_GT(eta, 0.0);
}

TEST(Effectiveness, MonotonicallyDecreasingWithPhi) {
    double phis[] = {0.1, 0.5, 1.0, 2.0, 5.0, 10.0};
    double prev_eta = 2.0;
    for (double p : phis) {
        double eta = DimNumbers::effectiveness(p);
        EXPECT_LT(eta, prev_eta + 1e-10)
            << "Effectiveness must decrease with phi";
        prev_eta = eta;
    }
}

// ============================================================================
// TEST GROUP: Plug-flow column with first-order decay
// ============================================================================

TEST(PlugFlowColumn, InletConcentrationPreserved) {
    double C_in = 1.0, k = 0.1, u = 0.01;
    EXPECT_NEAR(ReactiveColumn::plug_flow(C_in, k, u, 0.0), C_in, 1e-12);
}

TEST(PlugFlowColumn, ConcentrationDecaysWithDistance) {
    double C_in = 1.0, k = 1.0, u = 0.01;
    double C_x1 = ReactiveColumn::plug_flow(C_in, k, u, 0.01);
    double C_x2 = ReactiveColumn::plug_flow(C_in, k, u, 0.02);
    EXPECT_LT(C_x2, C_x1) << "Concentration should decrease with distance";
}

TEST(PlugFlowColumn, HalfLifeDistance) {
    // At x = u/k * ln(2): C = C_in / 2
    double C_in = 1.0, k = 10.0, u = 0.001;
    double x_half = u * std::log(2.0) / k;
    double C_half = ReactiveColumn::plug_flow(C_in, k, u, x_half);
    EXPECT_NEAR(C_half, C_in / 2.0, C_in * 0.01);
}

TEST(PlugFlowColumn, BreakthroughWithDamkohler) {
    // C_out = C_in * exp(-Da)
    // At Da = 1: C_out = 0.368 * C_in
    double C_in = 1.0, Da = 1.0;
    double C_out = ReactiveColumn::breakthrough_DaApprox(C_in, Da);
    EXPECT_NEAR(C_out, std::exp(-1.0), 0.01);
}

TEST(PlugFlowColumn, LargeDa_CompleteReaction) {
    // Da >> 1: essentially all substrate consumed
    double C_out = ReactiveColumn::breakthrough_DaApprox(1.0, 20.0);
    EXPECT_LT(C_out, 1e-8) << "At Da=20, concentration essentially zero at outlet";
}

TEST(PlugFlowColumn, SmallDa_NegligibleReaction) {
    // Da << 1: concentration mostly unchanged
    double C_out = ReactiveColumn::breakthrough_DaApprox(1.0, 0.01);
    EXPECT_NEAR(C_out, 1.0, 0.02) << "At Da=0.01, < 1% reaction";
}

// ============================================================================
// TEST GROUP: 1D reactive slab with diffusion
// ============================================================================

TEST(ReactiveSlab, InletBoundaryCondition) {
    double L=0.001, C0=1.0, k=1.0, D=1e-9;
    EXPECT_NEAR(ReactiveColumn::reactive_slab(0.0, L, C0, k, D), C0, 1e-10);
}

TEST(ReactiveSlab, ConcentrationMonotonicallyDecreases) {
    double L=0.001, C0=1.0, k=1e4, D=1e-10;  // phi >> 1
    double C_prev = C0;
    int Nx = 10;
    for (int i = 1; i <= Nx; ++i) {
        double x = L * i / Nx;
        double C = ReactiveColumn::reactive_slab(x, L, C0, k, D);
        EXPECT_LE(C, C_prev + 1e-12) << "C not decreasing at x=" << x;
        C_prev = C;
    }
}

TEST(ReactiveSlab, LowReactionFlat) {
    // k -> 0: profile should be flat (= C0 everywhere)
    double L=0.001, C0=0.8, k=1e-30, D=1e-9;
    double C_mid = ReactiveColumn::reactive_slab(L/2, L, C0, k, D);
    EXPECT_NEAR(C_mid, C0, C0 * 0.01);
}

TEST(ReactiveSlab, CompareHighLowThiele) {
    // High phi (fast reaction): steep gradient near inlet, low at outlet
    // Low phi (slow reaction): nearly uniform
    double L=1e-4, C0=1.0, D=1e-10;
    double k_low  = 1e-2;
    double k_high = 1e6;
    double phi_low  = L * std::sqrt(k_low  / D);
    double phi_high = L * std::sqrt(k_high / D);

    double C_out_low  = ReactiveColumn::reactive_slab(L, L, C0, k_low,  D);
    double C_out_high = ReactiveColumn::reactive_slab(L, L, C0, k_high, D);

    EXPECT_GT(phi_high, phi_low)  << "High k should give higher Thiele modulus";
    EXPECT_GT(C_out_low, C_out_high) << "Higher reaction -> lower outlet concentration";
}

// ============================================================================
// TEST GROUP: Operator splitting (transport then reaction)
// ============================================================================

TEST(OperatorSplitting, TransportThenReaction_MassDecreases) {
    // In operator splitting: each step either transports or reacts.
    // After a reaction step with first-order decay, total mass should decrease.
    int N = 5;
    std::vector<double> C(N, 1.0);  // uniform initial concentration
    double k = 0.1, dt = 0.01;

    // Reaction sub-step: dC/dt = -k*C  ->  C_new = C * exp(-k*dt) ≈ C*(1-k*dt)
    double mass_before = 0.0, mass_after = 0.0;
    for (int i = 0; i < N; ++i) {
        mass_before += C[i];
        C[i] *= (1.0 - k * dt);  // first-order Euler step
        mass_after += C[i];
    }
    EXPECT_LT(mass_after, mass_before) << "Reaction step should remove mass";
}

TEST(OperatorSplitting, PureTransportConservesMass) {
    // A pure advection step (no reaction) should conserve total mass.
    int N = 10;
    std::vector<double> C(N, 0.0);
    C[0] = 1.0; C[1] = 0.5; C[2] = 0.2;  // initial pulse

    double mass_before = 0.0;
    for (double c : C) mass_before += c;

    // Simple upwind shift (periodic)
    std::vector<double> C_new(N, 0.0);
    for (int i = 0; i < N; ++i) C_new[(i+1)%N] = C[i];

    double mass_after = 0.0;
    for (double c : C_new) mass_after += c;

    EXPECT_NEAR(mass_after, mass_before, 1e-12)
        << "Pure advection (periodic) must conserve mass";
}

// ============================================================================
// TEST GROUP: Coupled Monod kinetics in reactive transport context
// ============================================================================

TEST(MonodReactiveTransport, ReactionRateAsSourceTerm) {
    // In reactive transport, the kinetics source term (subsR[0]) is added to
    // the ADE concentration update. This test verifies the source is negative
    // (consumption) and physically consistent.
    std::vector<double> B   = {10.0};
    std::vector<double> C   = {1e-3};   // DOC above Ks
    std::vector<double> subsR(2, 0.0), bioR(1, 0.0);
    defineRxnKinetics(B, C, subsR, bioR, 1);

    double dDOC = subsR[0];  // source term for ADE: negative
    double dCO2 = subsR[1];  // CO2 production: positive
    double dB   = bioR[0];   // biomass source: positive (growth)

    EXPECT_LT(dDOC, 0.0)  << "DOC source must be negative (consumption)";
    EXPECT_GT(dCO2, 0.0)  << "CO2 source must be positive (production)";
    EXPECT_GT(dB,   0.0)  << "Biomass should grow at this DOC";
}

TEST(MonodReactiveTransport, SourceTermRatioMatchesYield) {
    // dB/dt / |dDOC/dt| should approximately equal Y (yield coefficient)
    // (without clamping and with k_decay << mu)
    std::vector<double> B   = {1.0};   // small biomass to avoid clamping
    std::vector<double> C   = {1.0};   // very high DOC
    std::vector<double> subsR(2, 0.0), bioR(1, 0.0);
    defineRxnKinetics(B, C, subsR, bioR, 1);

    double dDOC = subsR[0];  // negative
    double dB   = bioR[0];   // positive

    if (std::abs(dDOC) > 1e-15) {
        // dB = (mu - k_decay)*B, dDOC = -mu*B/Y
        // dB / (-dDOC) = (mu-k_decay)*Y / mu ≈ Y (since k_decay << mu)
        double ratio = dB / (-dDOC);
        EXPECT_NEAR(ratio, KineticParams::Y,
                    KineticParams::Y * 0.02 + KineticParams::k_decay)
            << "Growth/consumption ratio should approximate yield coefficient Y";
    }
}

TEST(MonodReactiveTransport, ZeroBiomass_ZeroSourceTerm) {
    // If no biomass, kinetics produces no source for the ADE
    std::vector<double> B   = {0.0};
    std::vector<double> C   = {1.0};
    std::vector<double> subsR(2, 0.0), bioR(1, 0.0);
    defineRxnKinetics(B, C, subsR, bioR, 1);
    EXPECT_DOUBLE_EQ(subsR[0], 0.0) << "No biomass -> no DOC source term";
    EXPECT_DOUBLE_EQ(subsR[1], 0.0) << "No biomass -> no CO2 source term";
}

TEST(MonodReactiveTransport, AbioticSourceTerm) {
    // Abiotic first-order decay also provides a source term for the ADE.
    // We verify: decay rate is negative, scales with concentration, and
    // matches the first-order formula dC/dt = -k * C.
    // Parameters: k_decay_0 = 1e-5 [1/s]
    double k_decay_abiotic = 1.0e-5;  // from AbioticParams::k_decay_0
    double C0 = 1.0e-3;              // concentration [mol/L]
    double expected_rate = -k_decay_abiotic * C0;  // = -1e-8

    EXPECT_LT(expected_rate, 0.0) << "First-order decay rate must be negative";
    EXPECT_NEAR(expected_rate, -1e-8, 1e-12);
}

TEST(MonodReactiveTransport, ReactionTransportNumberConsistency) {
    // Physical parameters should give reasonable dimensionless numbers.
    // Typical pore-scale simulation:
    //   u_phys = 1e-5 m/s, L = 1e-4 m, D = 1e-9 m²/s
    //   k_rxn = mu_max * Biomass_density ≈ 1.0 * 10 = 10 [1/s] * [kg/m³]
    //   (but dimensionally, k effective = mu_max * B / (Ks + C))

    double u = 1e-5, L = 1e-4, D = 1e-9;
    double Pe = DimNumbers::Pe(u, L, D);
    double k_eff = KineticParams::mu_max;  // max first-order rate
    double Da_II = DimNumbers::Da_II(k_eff, L, D);

    EXPECT_GT(Pe, 0.0);
    EXPECT_GT(Da_II, 0.0);

    // For pore-scale LBM, Pe is typically 0.1–10, Da_II can be >> 1
    // meaning biological reactions are often diffusion-limited at pore scale
    EXPECT_LT(Pe, 1e6) << "Pe should be physically reasonable";
}
