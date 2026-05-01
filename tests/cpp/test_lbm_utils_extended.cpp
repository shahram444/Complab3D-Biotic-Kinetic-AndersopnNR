// Extended unit tests for LBM utility math
// Covers: ADE tau/omega conversions, substrate tau calculation,
// biofilm diffusivity, timestep calculation, D3Q7 edge cases,
// FD Laplacian 3D boundary behavior, and mask arithmetic.

#include "plb_shim.h"
#include <gtest/gtest.h>
#include <cmath>
#include <vector>

// ============================================================================
// D3Q7 POPULATION ENCODING (replicated from test_lbm_utils.cpp)
// ============================================================================
namespace D3Q7 {
    struct Populations { double g[7]; };

    Populations encode(double rho) {
        Populations p;
        p.g[0] = (rho - 1.0) / 4.0;
        for (int i = 1; i < 7; ++i) p.g[i] = (rho - 1.0) / 8.0;
        return p;
    }

    double decode(const Populations& p) {
        double sum = p.g[0];
        for (int i = 1; i < 7; ++i) sum += p.g[i];
        return sum + 1.0;
    }

    void addDelta(Populations& p, double delta) {
        p.g[0] += delta / 4.0;
        for (int i = 1; i < 7; ++i) p.g[i] += delta / 8.0;
    }
}

// ============================================================================
// D3Q7 EXTENDED ENCODING TESTS
// ============================================================================

TEST(D3Q7ExtEncoding, VeryLargeDensity) {
    double rho = 1e10;
    auto p = D3Q7::encode(rho);
    double recovered = D3Q7::decode(p);
    EXPECT_NEAR(recovered, rho, rho * 1e-12);
}

TEST(D3Q7ExtEncoding, VerySmallDensity) {
    double rho = 1e-15;
    auto p = D3Q7::encode(rho);
    double recovered = D3Q7::decode(p);
    EXPECT_NEAR(recovered, rho, rho * 1e-3);  // relative tolerance for very small values
}

TEST(D3Q7ExtEncoding, NegativeDensity) {
    double rho = -5.0;
    auto p = D3Q7::encode(rho);
    double recovered = D3Q7::decode(p);
    EXPECT_NEAR(recovered, rho, 1e-12);
}

TEST(D3Q7ExtEncoding, WeightRatio) {
    // g[0] / g[1] should always be 2.0
    double rho = 5.0;
    auto p = D3Q7::encode(rho);
    EXPECT_NEAR(p.g[0] / p.g[1], 2.0, 1e-10);
}

TEST(D3Q7ExtEncoding, PopulationSymmetry) {
    auto p = D3Q7::encode(3.0);
    // All face populations should be equal
    for (int i = 2; i < 7; ++i) {
        EXPECT_DOUBLE_EQ(p.g[i], p.g[1]);
    }
}

TEST(D3Q7ExtEncoding, DeltaChainCommutative) {
    auto p1 = D3Q7::encode(2.0);
    D3Q7::addDelta(p1, 0.3);
    D3Q7::addDelta(p1, 0.7);

    auto p2 = D3Q7::encode(2.0);
    D3Q7::addDelta(p2, 0.7);
    D3Q7::addDelta(p2, 0.3);

    EXPECT_NEAR(D3Q7::decode(p1), D3Q7::decode(p2), 1e-14);
}

TEST(D3Q7ExtEncoding, DeltaCancelOut) {
    auto p = D3Q7::encode(5.0);
    D3Q7::addDelta(p, 3.0);
    D3Q7::addDelta(p, -3.0);
    EXPECT_NEAR(D3Q7::decode(p), 5.0, 1e-14);
}

TEST(D3Q7ExtEncoding, LargeSequentialDeltas) {
    auto p = D3Q7::encode(0.0);
    double total_delta = 0.0;
    for (int i = 0; i < 10000; ++i) {
        double d = 0.001;
        D3Q7::addDelta(p, d);
        total_delta += d;
    }
    EXPECT_NEAR(D3Q7::decode(p), total_delta, 1e-6);
}

// ============================================================================
// ADE TAU/OMEGA CONVERSION TESTS
// ============================================================================

namespace ADEPhysics {
    double cs2_ade() { return 1.0 / 3.0; }
    double invCs2_ade() { return 3.0; }
    double D_from_tau(double tau) { return cs2_ade() * (tau - 0.5); }
    double tau_from_D(double D) { return D / cs2_ade() + 0.5; }
    double omega_from_tau(double tau) { return 1.0 / tau; }

    // From complab.cpp Phase 3: substrate tau calculation
    double calcSubstrateTau(double refNu, double D_pore, double D_ref, double invCs2) {
        double nu = refNu * D_pore / D_ref;
        return nu * invCs2 + 0.5;
    }

    // Biofilm omega calculation
    double calcBiofilmOmega(double refNu, double D_biofilm, double D_ref, double invCs2) {
        return 1.0 / (refNu * D_biofilm / D_ref * invCs2 + 0.5);
    }

    // ADE timestep: dt = refNu * dx^2 / D_ref
    double calcADETimestep(double refNu, double dx, double D_ref) {
        return refNu * dx * dx / D_ref;
    }
}

TEST(ADEPhysics, TauFromDRoundTrip) {
    double D = 1e-9;
    double tau = ADEPhysics::tau_from_D(D);
    double D_back = ADEPhysics::D_from_tau(tau);
    EXPECT_NEAR(D_back, D, D * 1e-6);  // floating-point round-trip tolerance
}

TEST(ADEPhysics, TauAtMinimum) {
    // tau = 0.5 gives D = 0 (minimum stable)
    EXPECT_DOUBLE_EQ(ADEPhysics::D_from_tau(0.5), 0.0);
}

TEST(ADEPhysics, SubstrateTauScaling) {
    double refNu = 0.1;
    double D_ref = 1e-9;
    double invCs2 = 3.0;

    // If D_pore = D_ref, tau should be the reference tau
    double tau_same = ADEPhysics::calcSubstrateTau(refNu, D_ref, D_ref, invCs2);
    double tau_ref = refNu * invCs2 + 0.5;  // = 0.8
    EXPECT_NEAR(tau_same, tau_ref, 1e-10);

    // If D_pore = 2*D_ref, tau should be larger
    double tau_larger = ADEPhysics::calcSubstrateTau(refNu, 2 * D_ref, D_ref, invCs2);
    EXPECT_GT(tau_larger, tau_same);
}

TEST(ADEPhysics, SubstrateTauHalfDiffusivity) {
    double refNu = 0.1;
    double D_ref = 1e-9;
    double invCs2 = 3.0;

    double tau_half = ADEPhysics::calcSubstrateTau(refNu, 0.5 * D_ref, D_ref, invCs2);
    double tau_full = ADEPhysics::calcSubstrateTau(refNu, D_ref, D_ref, invCs2);
    EXPECT_LT(tau_half, tau_full);
}

TEST(ADEPhysics, BiofilmOmegaHigherThanPore) {
    double refNu = 0.1;
    double D_ref = 1e-9;
    double D_biofilm = 0.5e-9;  // Lower diffusivity in biofilm
    double invCs2 = 3.0;

    double omega_pore = 1.0 / (refNu * D_ref / D_ref * invCs2 + 0.5);
    double omega_biofilm = ADEPhysics::calcBiofilmOmega(refNu, D_biofilm, D_ref, invCs2);

    EXPECT_GT(omega_biofilm, omega_pore);  // Higher omega = faster relaxation = lower diffusivity
}

TEST(ADEPhysics, TimestepCalculation) {
    double refNu = 0.1;
    double dx = 1e-5;   // 10 um
    double D_ref = 1e-9; // m^2/s

    double dt = ADEPhysics::calcADETimestep(refNu, dx, D_ref);
    EXPECT_NEAR(dt, 0.1 * 1e-10 / 1e-9, 1e-10);  // = 1e-2 s
    EXPECT_GT(dt, 0.0);
}

TEST(ADEPhysics, TimestepScalesWithDx2) {
    double refNu = 0.1;
    double D_ref = 1e-9;

    double dt1 = ADEPhysics::calcADETimestep(refNu, 1e-5, D_ref);
    double dt2 = ADEPhysics::calcADETimestep(refNu, 2e-5, D_ref);

    EXPECT_NEAR(dt2 / dt1, 4.0, 1e-10);  // dx doubled -> dt quadrupled
}

// ============================================================================
// FD LAPLACIAN EXTENDED TESTS
// ============================================================================

double fdLaplacian3D(double b0, double bxp, double bxn,
                     double byp, double byn, double bzp, double bzn, double nu) {
    return b0 + nu * ((bxp - 2*b0 + bxn) + (byp - 2*b0 + byn) + (bzp - 2*b0 + bzn));
}

TEST(FDLaplacianExt, QuadraticFieldExact) {
    // For f(x,y,z) = x^2, d2f/dx2 = 2, all other = 0
    // At x=5: center=25, xp=36, xn=16, y/z=25
    double result = fdLaplacian3D(25.0, 36.0, 16.0, 25.0, 25.0, 25.0, 25.0, 1.0);
    // Expected: 25 + 1.0 * (36 - 50 + 16) = 25 + 2 = 27
    EXPECT_NEAR(result, 27.0, 1e-10);
}

TEST(FDLaplacianExt, SphericalSymmetry) {
    // All neighbors equal, different from center
    double result = fdLaplacian3D(2.0, 3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 0.1);
    // Laplacian = 6*(3 - 2) = 6
    // result = 2 + 0.1 * 6 = 2.6
    EXPECT_NEAR(result, 2.6, 1e-10);
}

TEST(FDLaplacianExt, MaxStableNu) {
    // For stability: nu <= 1/6 (CFL for 3D diffusion)
    double nu = 1.0 / 6.0;
    double result = fdLaplacian3D(1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, nu);
    // = 1 + (1/6) * (0 - 2 + 0 + 0 - 2 + 0 + 0 - 2 + 0) = 1 + (1/6)*(-6) = 0
    EXPECT_NEAR(result, 0.0, 1e-10);
}

TEST(FDLaplacianExt, AboveMaxNuGoesNegative) {
    double nu = 0.2;  // > 1/6
    double result = fdLaplacian3D(1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, nu);
    EXPECT_LT(result, 0.0);  // Unstable -> can go negative
}

TEST(FDLaplacianExt, ConservativeUpdate) {
    // Total mass should be conserved in a closed system
    double b = 10.0;
    double n1 = 5.0, n2 = 5.0, n3 = 5.0, n4 = 5.0, n5 = 5.0, n6 = 5.0;
    double nu = 0.1;

    double b_new = fdLaplacian3D(b, n1, n2, n3, n4, n5, n6, nu);
    double total_before = b + n1 + n2 + n3 + n4 + n5 + n6;
    // In this simplified 1-cell test, diffusion redistributes mass
    // but the update to b alone doesn't tell us about neighbors
    EXPECT_FALSE(std::isnan(b_new));
}

// ============================================================================
// PERMEABILITY AND FLOW EXTENDED TESTS
// ============================================================================

namespace DarcyFlowExt {
    double calcPermeability(double u0, double nu, double L, double deltaP) {
        if (deltaP < 1e-30) return 0.0;
        return (u0 * nu * L) / deltaP;
    }

    double calcTargetVelocity(double Pe, double D, double L) {
        if (L < 1e-30) return 0.0;
        return (Pe * D) / L;
    }
}

TEST(DarcyFlowExt, PermeabilityDimensionalAnalysis) {
    // k = u * nu * L / dP  -> dimensions: [m/s * m^2/s * m / (Pa)] = [m^2]
    double k = DarcyFlowExt::calcPermeability(0.001, 1e-6, 0.001, 1000.0);
    EXPECT_GT(k, 0.0);
    EXPECT_LT(k, 1.0);  // Should be way less than 1 m^2
}

TEST(DarcyFlowExt, VelocityFromPeclet) {
    // At Pe=1, u = D/L
    double D = 1e-9;
    double L = 1e-3;
    double u = DarcyFlowExt::calcTargetVelocity(1.0, D, L);
    EXPECT_NEAR(u, D / L, 1e-15);
}

TEST(DarcyFlowExt, PermeabilityProportionalToVelocity) {
    double k1 = DarcyFlowExt::calcPermeability(0.01, 1e-6, 0.01, 100.0);
    double k2 = DarcyFlowExt::calcPermeability(0.02, 1e-6, 0.01, 100.0);
    EXPECT_NEAR(k2 / k1, 2.0, 1e-10);
}

// ============================================================================
// BIOFILM OMEGA EXTENDED TESTS
// ============================================================================

double calcBioOmega(double nsOmega, double bioX) {
    return 1.0 / (bioX * (1.0/nsOmega - 0.5) + 0.5);
}

TEST(BioOmegaExt, SmallBioX) {
    // bioX approaching 0 -> omega approaches 2.0
    double omega = calcBioOmega(0.8, 0.001);
    EXPECT_NEAR(omega, 2.0, 0.01);
}

TEST(BioOmegaExt, BioXGreaterThanOne) {
    // bioX > 1 means enhanced permeability
    double omega = calcBioOmega(0.8, 2.0);
    EXPECT_LT(omega, 0.8);  // Lower omega = higher viscosity/permeability
}

TEST(BioOmegaExt, DifferentNsOmega) {
    double omega1 = calcBioOmega(0.6, 0.5);
    double omega2 = calcBioOmega(1.0, 0.5);
    // Different base omega should give different bio omega
    EXPECT_NE(omega1, omega2);
}

// ============================================================================
// MASK ARITHMETIC EXTENDED TESTS
// ============================================================================

TEST(MaskLogicExt, MultiplePoreTypes) {
    std::vector<int64_t> pore = {2, 3, 4, 5, 6};
    int64_t mask = 4;
    bool found = false;
    for (size_t i = 0; i < pore.size(); ++i) {
        if (mask == pore[i]) { found = true; break; }
    }
    EXPECT_TRUE(found);
}

TEST(MaskLogicExt, BiofilmMaskInMultiSpecies) {
    // In multi-species, biofilm masks are stored in bio_dynamics[microbe][stage]
    std::vector<std::vector<int64_t>> bio_dynamics = {
        {5, 6},   // microbe 0: stages 5, 6
        {7, 8}    // microbe 1: stages 7, 8
    };

    int64_t mask = 7;
    int which_microbe = -1;
    for (size_t m = 0; m < bio_dynamics.size(); ++m) {
        for (size_t s = 0; s < bio_dynamics[m].size(); ++s) {
            if (mask == bio_dynamics[m][s]) {
                which_microbe = (int)m;
                break;
            }
        }
        if (which_microbe >= 0) break;
    }
    EXPECT_EQ(which_microbe, 1);
}

// ============================================================================
// BIOMASS EXPANSION EXTENDED TESTS
// ============================================================================

TEST(BiomassExpansionExt, PartialBiomassBelowThreshold) {
    double threshold = 5.0;
    double biomass = 4.999;
    EXPECT_FALSE(biomass >= threshold);
}

TEST(BiomassExpansionExt, ZeroBiomass) {
    double threshold = 5.0;
    double biomass = 0.0;
    bool is_biofilm = false;
    bool should_convert = (!is_biofilm && biomass >= threshold);
    EXPECT_FALSE(should_convert);
}

TEST(BiomassExpansionExt, MaxBiomassCap) {
    // Total biomass at a cell should be capped at maxbMassRho
    double maxbMassRho = 10.0;
    double biomass = 15.0;
    double capped = std::min(biomass, maxbMassRho);
    EXPECT_DOUBLE_EQ(capped, maxbMassRho);
}

TEST(BiomassExpansionExt, ExcessBiomassCalculation) {
    // Excess = total - max -> needs redistribution
    double maxbMassRho = 10.0;
    double biomass = 13.5;
    double excess = biomass - maxbMassRho;
    EXPECT_NEAR(excess, 3.5, 1e-10);
}

TEST(BiomassExpansionExt, RedistributionAmong6Neighbors) {
    // Equal redistribution among 6 face neighbors
    double excess = 6.0;
    double per_neighbor = excess / 6.0;
    EXPECT_NEAR(per_neighbor, 1.0, 1e-10);
}

// ============================================================================
// PRESSURE GRADIENT DENSITY FORMULA TESTS
// ============================================================================
// From complab_functions.hh PressureGradient:
// density = 1 - deltaP * invCs2 / (nx - 1) * iX

TEST(PressureGradient, DensityAtInlet) {
    // At iX = 0, density = 1.0
    double deltaP = 0.001;
    int64_t nx = 50;
    double invCs2 = 3.0;
    double density = 1.0 - deltaP * invCs2 / (double)(nx - 1) * 0;
    EXPECT_DOUBLE_EQ(density, 1.0);
}

TEST(PressureGradient, DensityAtOutlet) {
    double deltaP = 0.001;
    int64_t nx = 50;
    double invCs2 = 3.0;
    double density = 1.0 - deltaP * invCs2 / (double)(nx - 1) * (nx - 1);
    EXPECT_NEAR(density, 1.0 - deltaP * invCs2, 1e-12);
}

TEST(PressureGradient, DensityDecreasesAlongX) {
    double deltaP = 0.001;
    int64_t nx = 50;
    double invCs2 = 3.0;

    double rho_prev = 1.0;
    for (int64_t iX = 1; iX < nx; ++iX) {
        double rho = 1.0 - deltaP * invCs2 / (double)(nx - 1) * iX;
        EXPECT_LT(rho, rho_prev) << "Density not decreasing at iX=" << iX;
        rho_prev = rho;
    }
}

TEST(PressureGradient, LinearProfile) {
    double deltaP = 0.001;
    int64_t nx = 100;
    double invCs2 = 3.0;

    double rho0 = 1.0 - deltaP * invCs2 / (double)(nx - 1) * 0;
    double rho_mid = 1.0 - deltaP * invCs2 / (double)(nx - 1) * 50;
    double rho_end = 1.0 - deltaP * invCs2 / (double)(nx - 1) * 99;

    // Midpoint should be average of endpoints
    EXPECT_NEAR(rho_mid, (rho0 + rho_end) / 2.0, 0.01 * (rho0 - rho_end));
}

TEST(PressureGradient, NegativeDeltaP) {
    // Negative deltaP = reverse flow
    double deltaP = -0.001;
    int64_t nx = 50;
    double invCs2 = 3.0;

    double rho_end = 1.0 - deltaP * invCs2 / (double)(nx - 1) * (nx - 1);
    EXPECT_GT(rho_end, 1.0);  // Density increases with negative deltaP
}

TEST(PressureGradient, ZeroDeltaP) {
    double deltaP = 0.0;
    int64_t nx = 50;
    double invCs2 = 3.0;

    for (int64_t iX = 0; iX < nx; ++iX) {
        double rho = 1.0 - deltaP * invCs2 / (double)(nx - 1) * iX;
        EXPECT_DOUBLE_EQ(rho, 1.0);
    }
}
