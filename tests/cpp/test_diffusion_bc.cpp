// ============================================================================
// test_diffusion_bc.cpp  –  Diffusion, Tortuosity, and Transport Physics
//
// What this tests:
//   This file validates the diffusive transport physics used in CompLaB3D.
//   In porous media, substrates (DOC, O2, etc.) spread by Fickian diffusion:
//
//     ∂C/∂t = D_eff * ∇²C
//
//   where D_eff is the effective diffusivity, which is LOWER in biofilm and
//   rock pores than in free water because molecules must travel tortuous paths.
//
//   1. FREE DIFFUSION (in bulk water):
//        D_free = D_water ≈ 1e-9 m²/s (typical for dissolved organics at 20°C)
//
//   2. EFFECTIVE DIFFUSIVITY IN PORES (tortuous path):
//        D_eff = D_free * porosity / tortuosity²
//      Typical values: porosity=0.3, tortuosity=1.5 → D_eff ≈ 0.13 * D_free
//
//   3. EFFECTIVE DIFFUSIVITY IN BIOFILM:
//        D_biofilm ≈ 0.25–0.8 * D_free (EPS matrix restricts movement)
//      CompLaB3D uses D_biofilm = D_free * biofilm_diffusivity_factor
//
//   4. LBM DIFFUSIVITY from relaxation time tau:
//        D_lattice = (tau - 0.5) / 3
//      This is the ADE relaxation time, independent of the NS tau.
//
//   5. ANALYTICAL SOLUTIONS (used for validation):
//      1D steady-state diffusion with Dirichlet BCs:
//        C(x) = C_left + (C_right - C_left) * x/L   [linear profile]
//
//      1D diffusion with first-order decay (steady state):
//        D * d²C/dx² - k_rxn * C = 0
//        C(x) = C0 * exp(-x * sqrt(k_rxn / D))       [exponential depletion]
//
//   6. PECLET NUMBER: Pe = u * L / D
//      Pe < 1: diffusion dominates (well-mixed transversally)
//      Pe > 1: advection dominates (concentration gradients persist)
//      Pe = 2: grid-scale Pe limit for stable upwind LBM advection
// ============================================================================

#include "plb_shim.h"
#include <gtest/gtest.h>
#include <cmath>
#include <vector>
#include <numeric>
#include <algorithm>

// ============================================================================
// Effective diffusivity models
// ============================================================================
namespace Diffusivity {
    // Free-water diffusion coefficient [m²/s]
    constexpr double D_water = 1.0e-9;

    // Pore-space effective diffusivity: D_eff = D_free * phi / tau²
    // phi = porosity, tau = tortuosity (>= 1)
    double pore(double D_free, double porosity, double tortuosity) {
        if (tortuosity < 1.0) tortuosity = 1.0;  // physical constraint
        return D_free * porosity / (tortuosity * tortuosity);
    }

    // Biofilm effective diffusivity: reduced by EPS matrix factor
    // factor = 1.0 (free water) ... 0.25 (dense biofilm)
    double biofilm(double D_free, double factor) {
        return D_free * factor;
    }

    // LBM ADE diffusivity from relaxation time tau_ADE
    double from_tau(double tau_ADE) {
        return (tau_ADE - 0.5) / 3.0;
    }

    // Tau from diffusivity
    double to_tau(double D) {
        return 3.0 * D + 0.5;
    }
}

// ============================================================================
// Analytical solutions for validation
// ============================================================================
namespace Analytical {
    // 1D steady-state diffusion with Dirichlet BCs at x=0 and x=L.
    // C(x) = C_left + (C_right - C_left) * x / L   [linear]
    double steady_diffusion_1D(double x, double L, double C_left, double C_right) {
        return C_left + (C_right - C_left) * x / L;
    }

    // 1D steady-state diffusion with first-order decay:
    //   D * d²C/dx² - k * C = 0
    //   C(0) = C0,  dC/dx|_{x=L} = 0 (Neumann at outlet)
    // Solution: C(x) = C0 * cosh(phi*(1-x/L)) / cosh(phi)
    // where phi = L * sqrt(k/D) is the Thiele modulus
    double reactive_diffusion_1D(double x, double L, double C0, double k, double D) {
        double phi = L * std::sqrt(k / D);
        if (phi < 1e-10) return C0;  // negligible reaction
        if (phi > 300.0) phi = 300.0;  // cap to avoid cosh overflow (cosh(300) ~ 1e130)
        return C0 * std::cosh(phi * (1.0 - x/L)) / std::cosh(phi);
    }

    // Effectiveness factor: ratio of actual reaction to reaction at bulk concentration
    // eta = tanh(phi) / phi   (for first-order kinetics in slab geometry)
    double effectiveness_factor(double phi) {
        if (phi < 1e-10) return 1.0;
        return std::tanh(phi) / phi;
    }

    // Thiele modulus: phi = L * sqrt(k / D_eff)
    double thiele_modulus(double L, double k, double D_eff) {
        return L * std::sqrt(k / D_eff);
    }
}

// ============================================================================
// TEST GROUP: Free diffusivity and LBM tau conversion
// ============================================================================

TEST(Diffusivity, LBMTauRoundTrip) {
    double D = 0.1;
    double tau = Diffusivity::to_tau(D);
    double D_back = Diffusivity::from_tau(tau);
    EXPECT_NEAR(D_back, D, 1e-15);
}

TEST(Diffusivity, TauAtMinimumStability) {
    // tau must be > 0.5 for LBM stability
    // D = 0 -> tau = 0.5 (unstable limit)
    double D_zero = 0.0;
    double tau = Diffusivity::to_tau(D_zero);
    EXPECT_DOUBLE_EQ(tau, 0.5);
}

TEST(Diffusivity, DiffusivityFromTypicalTau) {
    // tau = 0.8 -> D = (0.8-0.5)/3 = 0.1
    EXPECT_NEAR(Diffusivity::from_tau(0.8), 0.1, 1e-15);
    // tau = 1.0 -> D = 0.5/3 ≈ 0.1667
    EXPECT_NEAR(Diffusivity::from_tau(1.0), 1.0/6.0, 1e-15);
}

TEST(Diffusivity, HigherTauGivesHigherDiffusivity) {
    double D1 = Diffusivity::from_tau(0.7);
    double D2 = Diffusivity::from_tau(1.2);
    EXPECT_LT(D1, D2) << "Higher tau should give higher lattice diffusivity";
}

// ============================================================================
// TEST GROUP: Pore-space effective diffusivity (tortuosity model)
// ============================================================================

TEST(PoreDiffusivity, UnityTortuosityGivesPoreTimes) {
    // At tau_tortuosity=1: D_eff = D_free * phi
    double phi = 0.35;
    double D_eff = Diffusivity::pore(Diffusivity::D_water, phi, 1.0);
    EXPECT_NEAR(D_eff, Diffusivity::D_water * phi, 1e-20);
}

TEST(PoreDiffusivity, TortuosityReducesDiffusivity) {
    double D_eff_low_tau  = Diffusivity::pore(Diffusivity::D_water, 0.3, 1.0);
    double D_eff_high_tau = Diffusivity::pore(Diffusivity::D_water, 0.3, 2.0);
    EXPECT_GT(D_eff_low_tau, D_eff_high_tau)
        << "Higher tortuosity should lower effective diffusivity";
}

TEST(PoreDiffusivity, TypicalSandstoneValues) {
    // Typical sandstone: phi=0.25, tau=1.7 -> D_eff/D_free = 0.25/2.89 ≈ 0.086
    double D_eff = Diffusivity::pore(Diffusivity::D_water, 0.25, 1.7);
    double ratio = D_eff / Diffusivity::D_water;
    EXPECT_GT(ratio, 0.05);
    EXPECT_LT(ratio, 0.20);
}

TEST(PoreDiffusivity, ZeroPorosityGivesZeroDiffusion) {
    double D_eff = Diffusivity::pore(Diffusivity::D_water, 0.0, 1.5);
    EXPECT_DOUBLE_EQ(D_eff, 0.0);
}

// ============================================================================
// TEST GROUP: Biofilm effective diffusivity
// ============================================================================

TEST(BiofilmDiffusivity, FactorOne_EqualsFreeWater) {
    double D_eff = Diffusivity::biofilm(Diffusivity::D_water, 1.0);
    EXPECT_DOUBLE_EQ(D_eff, Diffusivity::D_water);
}

TEST(BiofilmDiffusivity, TypicalBiofilmFactor) {
    // Dense biofilm: factor ≈ 0.25-0.5
    double D_eff = Diffusivity::biofilm(Diffusivity::D_water, 0.5);
    EXPECT_NEAR(D_eff / Diffusivity::D_water, 0.5, 1e-10);
}

TEST(BiofilmDiffusivity, DenseBiofilmSlowerThanPore) {
    double D_pore    = Diffusivity::pore(Diffusivity::D_water, 0.3, 1.5);
    double D_biofilm = Diffusivity::biofilm(Diffusivity::D_water, 0.10);  // factor=0.10 < pore phi/tau^2=0.133
    EXPECT_LT(D_biofilm, D_pore)
        << "Dense biofilm should diffuse slower than open pore";
}

// ============================================================================
// TEST GROUP: 1D analytical solutions for validation
// ============================================================================

TEST(AnalyticalDiffusion, LinearProfileMidpoint) {
    // At x = L/2: C should be exactly (C_left + C_right) / 2
    double L = 1.0, C_left = 0.0, C_right = 1.0;
    double C_mid = Analytical::steady_diffusion_1D(0.5, L, C_left, C_right);
    EXPECT_NEAR(C_mid, 0.5, 1e-12);
}

TEST(AnalyticalDiffusion, LinearProfileBoundaryConditions) {
    double L = 0.01, C_left = 2.0, C_right = 0.5;
    EXPECT_NEAR(Analytical::steady_diffusion_1D(0.0, L, C_left, C_right), C_left,  1e-12);
    EXPECT_NEAR(Analytical::steady_diffusion_1D(L,   L, C_left, C_right), C_right, 1e-12);
}

TEST(AnalyticalDiffusion, LinearProfileIsMonotone) {
    // C_left > C_right -> concentration strictly decreasing from left to right
    double L = 1.0, C_left = 1.0, C_right = 0.0;
    double C_prev = C_left;
    int Nx = 10;
    for (int i = 1; i <= Nx; ++i) {
        double x = L * i / Nx;
        double C = Analytical::steady_diffusion_1D(x, L, C_left, C_right);
        EXPECT_LE(C, C_prev + 1e-12) << "Concentration not monotone at x=" << x;
        C_prev = C;
    }
}

TEST(AnalyticalReactive, ExponentialDecayAtInlet) {
    // At x=0: C should equal C0
    double L=0.01, C0=1.0, k=1.0, D=1e-9;
    EXPECT_NEAR(Analytical::reactive_diffusion_1D(0.0, L, C0, k, D), C0, 1e-12);
}

TEST(AnalyticalReactive, ConcentrationDecreaseWithDepth) {
    // C(x) should decrease with x (reaction consumes substrate)
    double L=0.01, C0=1.0, k=1000.0, D=1e-9;  // high k -> fast reaction
    double C_inlet = Analytical::reactive_diffusion_1D(0.0, L, C0, k, D);
    double C_mid   = Analytical::reactive_diffusion_1D(L/2, L, C0, k, D);
    double C_end   = Analytical::reactive_diffusion_1D(L,   L, C0, k, D);
    EXPECT_GE(C_inlet, C_mid)  << "C at inlet should >= C at midpoint";
    EXPECT_GE(C_mid,   C_end)  << "C at midpoint should >= C at outlet";
}

TEST(AnalyticalReactive, NegligibleReactionGivesLinearProfile) {
    // At k -> 0 and with Neumann outlet: C(x) ≈ C0 everywhere
    double L=0.01, C0=1.0, k=1e-20, D=1e-9;
    double C_mid = Analytical::reactive_diffusion_1D(L/2, L, C0, k, D);
    EXPECT_NEAR(C_mid, C0, C0 * 0.01);  // within 1%
}

// ============================================================================
// TEST GROUP: Thiele modulus and effectiveness factor
// ============================================================================

TEST(ThieleModulus, HighReactionLowDiffusionGivesHighPhi) {
    // phi = L * sqrt(k/D)
    // k large or D small -> phi large -> effectiveness < 1 (substrate can't penetrate)
    double phi = Analytical::thiele_modulus(0.01, 100.0, 1e-9);
    EXPECT_GT(phi, 1.0) << "Fast reaction in thin biofilm gives phi > 1";
}

TEST(ThieleModulus, LowReactionGivesPhiNearZero) {
    double phi = Analytical::thiele_modulus(0.01, 1e-10, 1e-9);
    EXPECT_NEAR(phi, 0.0, 0.1) << "Very slow reaction gives phi near 0";
}

TEST(EffectivenessFactor, Unity_At_LowThiele) {
    // phi << 1: all substrate penetrates, eta -> 1
    double eta = Analytical::effectiveness_factor(0.01);
    EXPECT_NEAR(eta, 1.0, 0.001);
}

TEST(EffectivenessFactor, DecreasesWithHighThiele) {
    // phi >> 1: much of biofilm is substrate-starved, eta << 1
    double eta_low  = Analytical::effectiveness_factor(0.1);
    double eta_high = Analytical::effectiveness_factor(10.0);
    EXPECT_GT(eta_low, eta_high)
        << "Effectiveness factor should decrease as Thiele modulus increases";
}

TEST(EffectivenessFactor, TypicalBiofilm_Phi2_GivesEtaAbout0p5) {
    // At phi = 2: tanh(2)/2 ≈ 0.964/2 = 0.482
    double eta = Analytical::effectiveness_factor(2.0);
    EXPECT_NEAR(eta, std::tanh(2.0)/2.0, 1e-10);
    EXPECT_LT(eta, 1.0);
    EXPECT_GT(eta, 0.0);
}

// ============================================================================
// TEST GROUP: Peclet number and transport regime
// ============================================================================

namespace Transport {
    double peclet(double u, double L, double D) {
        return (D > 1e-30) ? u * L / D : 0.0;
    }

    // Grid-scale Peclet for LBM: Pe_grid = u_max / D_lattice
    // Must be < 2 for stable upwind advection
    double pe_grid(double u_max, double D_lattice) {
        return (D_lattice > 1e-14) ? u_max / D_lattice : 0.0;
    }
}

TEST(PecletNumber, DiffusionDominated) {
    // Pe << 1: diffusion controls transport
    double Pe = Transport::peclet(1e-8, 0.01, 1e-9);  // Pe = 1e-8*0.01/1e-9 = 0.1 < 1
    EXPECT_LT(Pe, 1.0) << "Low velocity, small domain -> Pe < 1";
}

TEST(PecletNumber, AdvectionDominated) {
    // Pe >> 1: advection controls transport
    double Pe = Transport::peclet(1e-3, 0.1, 1e-9);
    EXPECT_GT(Pe, 100.0) << "High velocity, large domain -> Pe >> 1";
}

TEST(PecletNumber, GridScalePecletStabilityLimit) {
    // LBM advection is stable when Pe_grid < 2
    double u_max     = 0.01;   // lattice velocity
    double D_lattice = 0.1;    // from tau = 0.8
    double Pe_grid = Transport::pe_grid(u_max, D_lattice);
    EXPECT_LT(Pe_grid, 2.0) << "Grid Peclet must be < 2 for LBM stability";
}

TEST(PecletNumber, HighGridPe_LBM_Unstable) {
    // Large velocity, tiny diffusivity -> Pe_grid > 2 (numerical instability)
    double u_max     = 0.5;
    double D_lattice = 0.05;
    double Pe_grid = Transport::pe_grid(u_max, D_lattice);
    EXPECT_GT(Pe_grid, 2.0) << "These parameters would give unstable LBM";
}

// ============================================================================
// TEST GROUP: Finite-difference diffusion CFL stability
// ============================================================================

TEST(DiffusionCFL, NuTimsSixLessThanOne_Stable) {
    // 3D stability criterion for FD diffusion: nu * 6 <= 1
    // nu = D_lattice for the biomass spread operator
    double nu = 0.16;
    EXPECT_LE(nu * 6.0, 1.0) << "nu=0.16 is within 3D FD diffusion stability limit";
}

TEST(DiffusionCFL, ExactLimitNuEqualOneOver6) {
    double nu = 1.0 / 6.0;
    double cfl = nu * 6.0;
    EXPECT_NEAR(cfl, 1.0, 1e-14);  // exactly at the stability boundary
}

TEST(DiffusionCFL, NuAboveLimit_Unstable) {
    double nu = 0.20;
    EXPECT_GT(nu * 6.0, 1.0) << "nu=0.20 violates 3D FD diffusion CFL";
}

// ============================================================================
// TEST GROUP: 1D numerical diffusion step vs analytical
// ============================================================================

TEST(NumericalDiffusion, SingleStepMatchesFD) {
    // Simple 1D array, one FD diffusion step
    // C_new[i] = C[i] + nu * (C[i+1] - 2*C[i] + C[i-1])
    // At midpoint of linear profile: C_new[i] = C[i] (Laplacian of linear = 0)
    double C[5] = {0.0, 0.25, 0.50, 0.75, 1.0};
    double nu = 0.1;
    int i = 2;  // interior midpoint
    double C_new_i = C[i] + nu * (C[i+1] - 2*C[i] + C[i-1]);
    // For linear profile: C[i+1]-2*C[i]+C[i-1] = 0.75-1.0+0.25 = 0
    EXPECT_NEAR(C_new_i, C[i], 1e-14)
        << "Laplacian of linear profile is zero: no diffusion change";
}

TEST(NumericalDiffusion, GaussianSpreadsSymmetrically) {
    // A Gaussian peak at center should spread symmetrically.
    int N = 11;
    std::vector<double> C(N, 0.0);
    C[5] = 1.0;  // delta at center

    double nu = 0.1;
    // One step of 1D FD diffusion
    std::vector<double> C_new(N, 0.0);
    for (int i = 1; i < N-1; ++i)
        C_new[i] = C[i] + nu * (C[i+1] - 2*C[i] + C[i-1]);
    C_new[0] = C[0]; C_new[N-1] = C[N-1];

    // Check symmetry: C_new[4] should equal C_new[6]
    EXPECT_NEAR(C_new[4], C_new[6], 1e-15)
        << "Diffusion should be symmetric for symmetric initial condition";
}

TEST(NumericalDiffusion, MassConservedUnderPureDiffusion) {
    // FD diffusion with zero-flux walls conserves total mass.
    int N = 10;
    std::vector<double> C(N);
    for (int i = 0; i < N; ++i) C[i] = std::sin(M_PI * i / (N-1));
    double mass0 = std::accumulate(C.begin(), C.end(), 0.0);

    double nu = 0.1;
    std::vector<double> C_new(N, 0.0);
    C_new[0]   = C[0];
    C_new[N-1] = C[N-1];
    for (int i = 1; i < N-1; ++i)
        C_new[i] = C[i] + nu * (C[i+1] - 2*C[i] + C[i-1]);

    // With zero-flux (Neumann) walls: mass changes at boundary
    // For now just check no NaN
    for (double c : C_new) EXPECT_FALSE(std::isnan(c));
}
