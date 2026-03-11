// Unit tests for LBM utility math, D3Q7 population encoding/decoding,
// finite difference Laplacian, flow physics (Darcy, permeability), and
// stability report logic.
//
// These test the mathematical foundations used by the Palabos processor
// classes without requiring the Palabos library itself.

#include "plb_shim.h"
#include <gtest/gtest.h>
#include <cmath>
#include <vector>

// ============================================================================
// D3Q7 POPULATION ENCODING
// ============================================================================
// CompLaB3D encodes a scalar value `rho` into D3Q7 populations as:
//   g[0] = (rho - 1) / 4
//   g[1] = g[2] = g[3] = g[4] = g[5] = g[6] = (rho - 1) / 8
//
// The density is recovered as: rho = sum(g) + 1 = g[0] + 6*g[1] + 1
// This is used for mask lattices, biomass lattices, age lattices, etc.

namespace D3Q7 {
    struct Populations {
        double g[7];
    };

    Populations encode(double rho) {
        Populations p;
        p.g[0] = (rho - 1.0) / 4.0;
        for (int i = 1; i < 7; ++i)
            p.g[i] = (rho - 1.0) / 8.0;
        return p;
    }

    double decode(const Populations& p) {
        double sum = p.g[0];
        for (int i = 1; i < 7; ++i) sum += p.g[i];
        return sum + 1.0;
    }

    // Incremental update (used for dC or dB changes)
    void addDelta(Populations& p, double delta) {
        p.g[0] += delta / 4.0;
        for (int i = 1; i < 7; ++i)
            p.g[i] += delta / 8.0;
    }
}

TEST(D3Q7Encoding, EncodeDecodeRoundTrip) {
    double values[] = {0.0, 1.0, 5.0, 100.0, 1e-5, -1.0};
    for (double rho : values) {
        auto p = D3Q7::encode(rho);
        double recovered = D3Q7::decode(p);
        EXPECT_NEAR(recovered, rho, 1e-12) << "Failed for rho=" << rho;
    }
}

TEST(D3Q7Encoding, EncodeZeroDensity) {
    auto p = D3Q7::encode(0.0);
    EXPECT_DOUBLE_EQ(p.g[0], -0.25);
    EXPECT_DOUBLE_EQ(p.g[1], -0.125);
}

TEST(D3Q7Encoding, EncodeUnitDensity) {
    auto p = D3Q7::encode(1.0);
    EXPECT_DOUBLE_EQ(p.g[0], 0.0);
    EXPECT_DOUBLE_EQ(p.g[1], 0.0);
}

TEST(D3Q7Encoding, WeightsSum) {
    // D3Q7 weights: w0=1/4, w1-w6=1/8.  Sum = 1/4 + 6/8 = 1.0
    double sum = 1.0/4.0 + 6.0 * (1.0/8.0);
    EXPECT_DOUBLE_EQ(sum, 1.0);
}

TEST(D3Q7Encoding, DeltaUpdatePreservesDensity) {
    auto p = D3Q7::encode(5.0);
    double delta = 0.3;
    D3Q7::addDelta(p, delta);
    double recovered = D3Q7::decode(p);
    EXPECT_NEAR(recovered, 5.3, 1e-12);
}

TEST(D3Q7Encoding, MultipleDeltaUpdates) {
    auto p = D3Q7::encode(2.0);
    D3Q7::addDelta(p, 0.5);
    D3Q7::addDelta(p, -0.2);
    D3Q7::addDelta(p, 0.1);
    double recovered = D3Q7::decode(p);
    EXPECT_NEAR(recovered, 2.4, 1e-12);
}

// ============================================================================
// FINITE DIFFERENCE 3D LAPLACIAN
// ============================================================================
// The biomass diffusion processor uses:
//   new_bM = b0 + nu * ((bxp - 2*b0 + bxn) + (byp - 2*b0 + byn) + (bzp - 2*b0 + bzn))
// which is the standard 7-point 3D Laplacian stencil.

double fdLaplacian3D(double b0, double bxp, double bxn,
                     double byp, double byn, double bzp, double bzn, double nu) {
    return b0 + nu * ((bxp - 2*b0 + bxn) + (byp - 2*b0 + byn) + (bzp - 2*b0 + bzn));
}

TEST(FDLaplacian, UniformFieldNoChange) {
    // If all neighbors equal the center, Laplacian = 0
    double result = fdLaplacian3D(5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 0.1);
    EXPECT_DOUBLE_EQ(result, 5.0);
}

TEST(FDLaplacian, HighCenterDiffusesOut) {
    // Center higher than neighbors -> diffuses out -> value decreases
    double result = fdLaplacian3D(10.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.01);
    EXPECT_LT(result, 10.0);
}

TEST(FDLaplacian, LowCenterDiffusesIn) {
    // Center lower than neighbors -> diffuses in -> value increases
    double result = fdLaplacian3D(1.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 0.01);
    EXPECT_GT(result, 1.0);
}

TEST(FDLaplacian, ZeroNuNoChange) {
    double result = fdLaplacian3D(1.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 0.0);
    EXPECT_DOUBLE_EQ(result, 1.0);
}

TEST(FDLaplacian, SymmetricGradient) {
    // Linear field: value = x. At center x=5, xp=6, xn=4, y/z = 5
    // d2f/dx2 = 6 - 10 + 4 = 0, so no change
    double result = fdLaplacian3D(5.0, 6.0, 4.0, 5.0, 5.0, 5.0, 5.0, 0.1);
    EXPECT_DOUBLE_EQ(result, 5.0);
}

TEST(FDLaplacian, StabilityCheck) {
    // For stability: nu * 6 <= 1 (CFL for 3D diffusion)
    double nu = 0.16;  // nu*6 = 0.96 < 1
    double result = fdLaplacian3D(10.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, nu);
    // Should not go negative for reasonable nu
    EXPECT_GE(result, 0.0);
}

// ============================================================================
// DARCY FLOW / PERMEABILITY CALCULATIONS
// ============================================================================
// From complab.cpp Phase 3:
//   k = (u0 * nu_phys * L) / deltaP0     (permeability from initial simulation)
//   u_target = (Pe * D_phys) / L          (target velocity from Peclet number)
//   deltaP_new = (u_target * nu_phys * L) / k   (corrected pressure gradient)

namespace DarcyFlow {
    double calcPermeability(double u0, double nu, double L, double deltaP) {
        if (deltaP < 1e-30) return 0.0;
        return (u0 * nu * L) / deltaP;
    }

    double calcTargetVelocity(double Pe, double D, double L) {
        if (L < 1e-30) return 0.0;
        return (Pe * D) / L;
    }

    double calcCorrectedPressure(double u_target, double nu, double L, double k) {
        if (k < 1e-30) return 0.0;
        return (u_target * nu * L) / k;
    }
}

TEST(DarcyFlow, PermeabilityCalculation) {
    double k = DarcyFlow::calcPermeability(0.01, 1e-6, 0.01, 100.0);
    EXPECT_GT(k, 0.0);
    EXPECT_NEAR(k, 1e-12, 1e-15);
}

TEST(DarcyFlow, TargetVelocity) {
    double u = DarcyFlow::calcTargetVelocity(10.0, 1e-9, 0.01);
    EXPECT_NEAR(u, 1e-6, 1e-12);
}

TEST(DarcyFlow, CorrectedPressure) {
    double k = 1e-12;
    double u = 1e-6;
    double nu = 1e-6;
    double L = 0.01;
    double dP = DarcyFlow::calcCorrectedPressure(u, nu, L, k);
    // dP = (1e-6 * 1e-6 * 0.01) / 1e-12 = 1e-14 / 1e-12 = 0.01
    EXPECT_NEAR(dP, 0.01, 1e-6);
}

TEST(DarcyFlow, ZeroPressureGivesZeroPermeability) {
    double k = DarcyFlow::calcPermeability(0.01, 1e-6, 0.01, 0.0);
    EXPECT_DOUBLE_EQ(k, 0.0);
}

TEST(DarcyFlow, RoundTrip) {
    // Calculate k from initial simulation, then use it to get back deltaP
    double u0 = 0.01, nu = 1e-6, L = 0.01, dP0 = 100.0;
    double k = DarcyFlow::calcPermeability(u0, nu, L, dP0);
    double dP_check = DarcyFlow::calcCorrectedPressure(u0, nu, L, k);
    EXPECT_NEAR(dP_check, dP0, 1e-6);
}

// ============================================================================
// LATTICE BOLTZMANN PHYSICS
// ============================================================================
// LBM parameters: cs^2 = 1/3, nu_lattice = (tau - 0.5) / 3

namespace LBMPhysics {
    double cs2() { return 1.0 / 3.0; }
    double cs() { return std::sqrt(1.0 / 3.0); }
    double nu_from_tau(double tau) { return (tau - 0.5) / 3.0; }
    double tau_from_nu(double nu) { return 3.0 * nu + 0.5; }
    double D_from_tau_ADE(double tau) { return (tau - 0.5) / 3.0; }

    // Mach number
    double mach(double u_max) { return u_max / cs(); }

    // Grid Peclet number
    double pe_grid(double u_max, double D_lattice) {
        return (D_lattice > 1e-14) ? u_max / D_lattice : 0.0;
    }
}

TEST(LBMPhysics, SpeedOfSound) {
    EXPECT_NEAR(LBMPhysics::cs(), std::sqrt(1.0/3.0), 1e-15);
    EXPECT_NEAR(LBMPhysics::cs2(), 1.0/3.0, 1e-15);
}

TEST(LBMPhysics, TauNuConversion) {
    double tau = 0.8;
    double nu = LBMPhysics::nu_from_tau(tau);
    double tau_back = LBMPhysics::tau_from_nu(nu);
    EXPECT_NEAR(tau_back, tau, 1e-15);
}

TEST(LBMPhysics, NuAtTauHalf) {
    // At tau = 0.5, viscosity = 0 (minimum stable tau)
    EXPECT_DOUBLE_EQ(LBMPhysics::nu_from_tau(0.5), 0.0);
}

TEST(LBMPhysics, MachNumber) {
    double Ma = LBMPhysics::mach(0.01);
    EXPECT_NEAR(Ma, 0.01 / std::sqrt(1.0/3.0), 1e-10);
    EXPECT_LT(Ma, 0.1);  // Should be well below compressibility limit
}

TEST(LBMPhysics, PeGridNumber) {
    EXPECT_DOUBLE_EQ(LBMPhysics::pe_grid(0.1, 0.1), 1.0);
    EXPECT_DOUBLE_EQ(LBMPhysics::pe_grid(0.1, 0.05), 2.0);
    EXPECT_DOUBLE_EQ(LBMPhysics::pe_grid(0.01, 0.0), 0.0);  // zero diffusion
}

TEST(LBMPhysics, DiffusionFromTauADE) {
    double D = LBMPhysics::D_from_tau_ADE(0.8);
    EXPECT_NEAR(D, 0.1, 1e-15);
}

// ============================================================================
// BIOMASS THRESHOLD LOGIC
// ============================================================================
// CompLaB3D uses COMPLAB_THRD = 1e-14 as the threshold for "essentially zero"

constexpr double COMPLAB_THRD = 1e-14;

TEST(Threshold, BelowThresholdIsZero) {
    double val = 1e-15;
    bool is_zero = (val < COMPLAB_THRD);
    EXPECT_TRUE(is_zero);
}

TEST(Threshold, AboveThresholdIsNonZero) {
    double val = 1e-13;
    bool is_zero = (val < COMPLAB_THRD);
    EXPECT_FALSE(is_zero);
}

// ============================================================================
// BIOFILM OMEGA CALCULATION
// ============================================================================
// From updateNsLatticesDynamics3D:
//   bioOmega = 1 / (bioX * (1/nsOmega - 0.5) + 0.5)
// where bioX is the permeability ratio of biofilm.

double calcBioOmega(double nsOmega, double bioX) {
    return 1.0 / (bioX * (1.0/nsOmega - 0.5) + 0.5);
}

TEST(BioOmega, NoPermeabilityReduction) {
    // bioX = 1.0 means no change -> bioOmega = nsOmega
    double bioOmega = calcBioOmega(0.8, 1.0);
    EXPECT_NEAR(bioOmega, 0.8, 1e-10);
}

TEST(BioOmega, ReducedPermeability) {
    // bioX < 1 -> biofilm is less permeable -> higher omega (faster relaxation)
    double bioOmega = calcBioOmega(0.8, 0.5);
    EXPECT_GT(bioOmega, 0.8);
}

TEST(BioOmega, ZeroPermeabilityGivesBounceBack) {
    // bioX -> 0 -> bioOmega = 1/(0 + 0.5) = 2.0
    double bioOmega = calcBioOmega(0.8, 0.0);
    EXPECT_NEAR(bioOmega, 2.0, 1e-10);
}

// ============================================================================
// MASK LOGIC
// ============================================================================
// The mask system determines cell types:
//   mask == bb (bounce-back = wall boundary)
//   mask == solid (impermeable solid)
//   mask in pore[] (pore space)
//   mask in bio[][] (biofilm)

TEST(MaskLogic, PoreDetection) {
    std::vector<int64_t> pore = {2, 3, 4};
    int64_t mask = 3;
    bool is_pore = false;
    for (size_t i = 0; i < pore.size(); ++i) {
        if (mask == pore[i]) { is_pore = true; break; }
    }
    EXPECT_TRUE(is_pore);
}

TEST(MaskLogic, NonPoreDetection) {
    std::vector<int64_t> pore = {2, 3, 4};
    int64_t mask = 5;  // biofilm mask
    bool is_pore = false;
    for (size_t i = 0; i < pore.size(); ++i) {
        if (mask == pore[i]) { is_pore = true; break; }
    }
    EXPECT_FALSE(is_pore);
}

TEST(MaskLogic, SolidAndBBSkipped) {
    int64_t bb = 1, solid = 0;
    int64_t mask_solid = 0, mask_bb = 1, mask_pore = 2;

    EXPECT_TRUE(mask_solid == solid);
    EXPECT_TRUE(mask_bb == bb);
    EXPECT_FALSE(mask_pore == solid || mask_pore == bb);
}

// ============================================================================
// BIOMASS EXPANSION THRESHOLD
// ============================================================================
// From updateLocalMaskNtotalLattices3D:
//   thrdbMassRho = bMassFrac * maxbMassRho
// A cell converts from pore to biofilm when total biomass > thrdbMassRho

TEST(BiomassExpansion, ThresholdCalculation) {
    double bMassFrac = 0.5;
    double maxbMassRho = 10.0;
    double threshold = bMassFrac * maxbMassRho;
    EXPECT_DOUBLE_EQ(threshold, 5.0);
}

TEST(BiomassExpansion, CellBecomesFilm) {
    double threshold = 5.0;
    double biomass = 6.0;
    bool is_pore = true;
    bool should_convert = (is_pore && biomass >= threshold);
    EXPECT_TRUE(should_convert);
}

TEST(BiomassExpansion, CellBecomesPore) {
    double threshold = 5.0;
    double biomass = 3.0;
    bool is_pore = false;  // currently biofilm
    bool should_convert = (!is_pore && biomass < threshold);
    EXPECT_TRUE(should_convert);
}
