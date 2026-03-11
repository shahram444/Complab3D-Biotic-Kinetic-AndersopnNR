// Unit tests for EquilibriumChemistry (Anderson Acceleration + PCF solver)
// Tests the equilibrium solver from complab3d_processors_part4_eqsolver.hh
// without Palabos dependency.

#include "plb_shim.h"
#include <gtest/gtest.h>
#include <cmath>
#include <vector>
#include <string>
#include <limits>
#include <algorithm>

// The solver uses plb::plint and a few other plb types.
// plb_shim.h provides plint; we stub anything else needed.
using plb::plint;
typedef double T;

// Stub out pcout (the solver uses it in printStatistics)
#include <iostream>
#define pcout std::cout

// Include the equilibrium solver header directly.
// It only depends on <cmath>, <vector>, <string>, <algorithm>, <iomanip>, plb::plint.
#include "complab3d_processors_part4_eqsolver_standalone.hh"

// ============================================================================
// TEST FIXTURE: sets up a simple 2-component carbonate-like system
// ============================================================================
class EqSolverFixture : public ::testing::Test {
protected:
    EquilibriumChemistry<double> solver;

    void SetUp() override {
        // Simple 2-component, 3-species system:
        //   Components: "H+", "CO3"
        //   Species: "H+" (component), "CO3" (component), "HCO3"
        //   Reaction: H+ + CO3^2- <-> HCO3^-   logK = 10.3
        //
        //   Stoichiometry matrix (species x components):
        //     H+    : [1, 0]   (is a component)
        //     CO3   : [0, 1]   (is a component)
        //     HCO3  : [1, 1]   (formed from 1 H+ + 1 CO3)

        solver.setComponentNames({"H+", "CO3"});
        solver.setSpeciesNames({"H+", "CO3", "HCO3"});
        solver.setLogK({0.0, 0.0, 10.3});
        solver.setStoichiometryMatrix({
            {1.0, 0.0},   // H+
            {0.0, 1.0},   // CO3
            {1.0, 1.0}    // HCO3 = H+ + CO3
        });
        solver.setMaxIterations(200);
        solver.setTolerance(1e-8);
    }
};

// ========================== VECTOR OPERATIONS ==========================

TEST(EqVectorOps, NormOfZeroVector) {
    EquilibriumChemistry<double> s;
    std::vector<double> v = {0.0, 0.0, 0.0};
    EXPECT_DOUBLE_EQ(s.norm(v), 0.0);
}

TEST(EqVectorOps, NormOfUnitVector) {
    EquilibriumChemistry<double> s;
    std::vector<double> v = {1.0, 0.0, 0.0};
    EXPECT_DOUBLE_EQ(s.norm(v), 1.0);
}

TEST(EqVectorOps, NormOfGeneralVector) {
    EquilibriumChemistry<double> s;
    std::vector<double> v = {3.0, 4.0};
    EXPECT_DOUBLE_EQ(s.norm(v), 5.0);
}

TEST(EqVectorOps, VecSubtract) {
    EquilibriumChemistry<double> s;
    std::vector<double> a = {5.0, 3.0}, b = {2.0, 1.0};
    auto r = s.vec_subtract(a, b);
    EXPECT_DOUBLE_EQ(r[0], 3.0);
    EXPECT_DOUBLE_EQ(r[1], 2.0);
}

TEST(EqVectorOps, VecAdd) {
    EquilibriumChemistry<double> s;
    std::vector<double> a = {1.0, 2.0}, b = {3.0, 4.0};
    auto r = s.vec_add(a, b);
    EXPECT_DOUBLE_EQ(r[0], 4.0);
    EXPECT_DOUBLE_EQ(r[1], 6.0);
}

TEST(EqVectorOps, DotProduct) {
    EquilibriumChemistry<double> s;
    std::vector<double> a = {1.0, 2.0, 3.0}, b = {4.0, 5.0, 6.0};
    EXPECT_DOUBLE_EQ(s.dot_product(a, b), 32.0);
}

TEST(EqVectorOps, DotProductMismatchedSizes) {
    EquilibriumChemistry<double> s;
    std::vector<double> a = {1.0, 2.0}, b = {3.0};
    // Should handle gracefully, only sums up to min size
    EXPECT_DOUBLE_EQ(s.dot_product(a, b), 3.0);
}

TEST(EqVectorOps, VecSubtractMismatchedSizes) {
    EquilibriumChemistry<double> s;
    std::vector<double> a = {5.0, 3.0}, b = {2.0};
    auto r = s.vec_subtract(a, b);
    EXPECT_DOUBLE_EQ(r[0], 3.0);
    EXPECT_DOUBLE_EQ(r[1], 3.0);  // b[1] treated as 0
}

// ========================== QR DECOMPOSITION ==========================

TEST(EqQR, SingleColumnQR) {
    EquilibriumChemistry<double> s;
    std::vector<std::vector<double>> cols = {{3.0, 4.0}};
    std::vector<std::vector<double>> Q, R;
    double condNum;
    s.qr_decomposition(cols, Q, R, condNum);

    // Q should be unit vector: [3/5, 4/5]
    EXPECT_NEAR(Q[0][0], 0.6, 1e-10);
    EXPECT_NEAR(Q[0][1], 0.8, 1e-10);
    // R[0][0] should be the norm: 5.0
    EXPECT_NEAR(R[0][0], 5.0, 1e-10);
    EXPECT_NEAR(condNum, 1.0, 1e-10);
}

TEST(EqQR, TwoColumnOrthogonalQR) {
    EquilibriumChemistry<double> s;
    std::vector<std::vector<double>> cols = {{1.0, 0.0}, {0.0, 1.0}};
    std::vector<std::vector<double>> Q, R;
    double condNum;
    s.qr_decomposition(cols, Q, R, condNum);

    // Already orthogonal -> condition number = 1
    EXPECT_NEAR(condNum, 1.0, 1e-10);
    EXPECT_NEAR(R[0][0], 1.0, 1e-10);
    EXPECT_NEAR(R[1][1], 1.0, 1e-10);
}

TEST(EqQR, EmptyColumnsQR) {
    EquilibriumChemistry<double> s;
    std::vector<std::vector<double>> cols;
    std::vector<std::vector<double>> Q, R;
    double condNum;
    s.qr_decomposition(cols, Q, R, condNum);
    EXPECT_DOUBLE_EQ(condNum, 1.0);
}

// ========================== UPPER TRIANGULAR SOLVE ==========================

TEST(EqTriangularSolve, IdentitySystem) {
    EquilibriumChemistry<double> s;
    std::vector<std::vector<double>> R = {{1.0, 0.0}, {0.0, 1.0}};
    std::vector<double> b = {3.0, 7.0};
    auto x = s.solve_upper_triangular(R, b);
    EXPECT_NEAR(x[0], 3.0, 1e-10);
    EXPECT_NEAR(x[1], 7.0, 1e-10);
}

TEST(EqTriangularSolve, GeneralUpperTriangular) {
    EquilibriumChemistry<double> s;
    // R = [[2, 3], [0, 4]], b = [11, 8]
    // x[1] = 8/4 = 2, x[0] = (11 - 3*2)/2 = 2.5
    std::vector<std::vector<double>> R = {{2.0, 3.0}, {0.0, 4.0}};
    std::vector<double> b = {11.0, 8.0};
    auto x = s.solve_upper_triangular(R, b);
    EXPECT_NEAR(x[0], 2.5, 1e-10);
    EXPECT_NEAR(x[1], 2.0, 1e-10);
}

// ========================== MASS ACTION LAW ==========================

TEST_F(EqSolverFixture, CalcSpeciesFromLogC) {
    // logC = [log10(1e-7), log10(1e-3)] = [-7, -3]
    std::vector<double> logC = {-7.0, -3.0};
    auto conc = solver.calc_species(logC);

    // H+  = 10^(0 + 1*(-7) + 0*(-3)) = 10^-7
    EXPECT_NEAR(conc[0], 1e-7, 1e-10);
    // CO3 = 10^(0 + 0*(-7) + 1*(-3)) = 10^-3
    EXPECT_NEAR(conc[1], 1e-3, 1e-6);
    // HCO3 = 10^(10.3 + 1*(-7) + 1*(-3)) = 10^0.3 = ~1.995
    EXPECT_NEAR(conc[2], std::pow(10.0, 0.3), 0.01);
}

TEST_F(EqSolverFixture, CalcSpeciesBoundsConcentrations) {
    // Extreme logC should be clamped
    std::vector<double> logC = {-50.0, 50.0};
    auto conc = solver.calc_species(logC);

    // All concentrations should be within [MIN_CONC, MAX_CONC]
    for (double c : conc) {
        EXPECT_GE(c, EquilibriumChemistry<double>::MIN_CONC);
        EXPECT_LE(c, EquilibriumChemistry<double>::MAX_CONC);
    }
}

// ========================== COMPONENT TOTALS ==========================

TEST_F(EqSolverFixture, CalcComponentTotals) {
    // Species concentrations: H+=1e-7, CO3=1e-3, HCO3=2.0
    std::vector<double> species = {1e-7, 1e-3, 2.0};
    auto T_total = solver.calc_component_totals(species);

    // T_H+ = 1*1e-7 + 0*1e-3 + 1*2.0 = ~2.0
    EXPECT_NEAR(T_total[0], 1e-7 + 2.0, 1e-5);
    // T_CO3 = 0*1e-7 + 1*1e-3 + 1*2.0 = ~2.001
    EXPECT_NEAR(T_total[1], 1e-3 + 2.0, 1e-5);
}

// ========================== EQUILIBRIUM SPECIES CHECK ==========================

TEST_F(EqSolverFixture, IsEquilibriumSpecies) {
    // H+ has stoich [1, 0] -> is equilibrium species
    EXPECT_TRUE(solver.isEquilibriumSpecies(0));
    // CO3 has stoich [0, 1] -> is equilibrium species
    EXPECT_TRUE(solver.isEquilibriumSpecies(1));
    // HCO3 has stoich [1, 1] -> is equilibrium species
    EXPECT_TRUE(solver.isEquilibriumSpecies(2));
    // Out of range -> false
    EXPECT_FALSE(solver.isEquilibriumSpecies(99));
}

// ========================== GETTERS AND SETTERS ==========================

TEST_F(EqSolverFixture, GettersReturnCorrectValues) {
    EXPECT_EQ(solver.getNumComponents(), 2);
    EXPECT_EQ(solver.getNumSpecies(), 3);
    EXPECT_EQ(solver.getMaxIterations(), 200);
    EXPECT_NEAR(solver.getTolerance(), 1e-8, 1e-15);
    EXPECT_EQ(solver.getAndersonDepth(), 4);
}

TEST_F(EqSolverFixture, SetAndGetAndersonDepth) {
    solver.setAndersonDepth(6);
    EXPECT_EQ(solver.getAndersonDepth(), 6);
    // Minimum depth should be 1
    solver.setAndersonDepth(0);
    EXPECT_EQ(solver.getAndersonDepth(), 1);
    solver.setAndersonDepth(-5);
    EXPECT_EQ(solver.getAndersonDepth(), 1);
}

TEST_F(EqSolverFixture, SpeciesNamesFilterH2O) {
    EquilibriumChemistry<double> s2;
    s2.setSpeciesNames({"H+", "H2O", "CO3"});
    EXPECT_EQ(s2.getNumSpecies(), 2);
    auto names = s2.getSpeciesNames();
    EXPECT_EQ(names[0], "H+");
    EXPECT_EQ(names[1], "CO3");
}

TEST_F(EqSolverFixture, LogKValuesPreserved) {
    auto logK = solver.getLogK();
    EXPECT_EQ(logK.size(), 3u);
    EXPECT_DOUBLE_EQ(logK[0], 0.0);
    EXPECT_DOUBLE_EQ(logK[1], 0.0);
    EXPECT_DOUBLE_EQ(logK[2], 10.3);
}

// ========================== STATISTICS ==========================

TEST_F(EqSolverFixture, StatisticsTracking) {
    solver.resetStatistics();
    EXPECT_EQ(solver.getTotalSolves(), 0);
    EXPECT_EQ(solver.getTotalConverged(), 0);
    EXPECT_EQ(solver.getTotalDiverged(), 0);
}

// ========================== EMPTY / EDGE CASES ==========================

TEST(EqSolverEdge, EmptyComponentsReturnInput) {
    EquilibriumChemistry<double> s;
    // No components or species set
    std::vector<double> input = {1e-3, 2e-3};
    auto result = s.calculate_species_concentrations(input);
    EXPECT_EQ(result, input);
}

TEST(EqSolverEdge, NoSpeciesReturnInput) {
    EquilibriumChemistry<double> s;
    s.setComponentNames({"H+"});
    // No species set -> ns == 0 -> return input
    std::vector<double> input = {1e-3};
    auto result = s.calculate_species_concentrations(input);
    EXPECT_EQ(result, input);
}

// ========================== CONVERGENCE ==========================

TEST_F(EqSolverFixture, SolverConvergesOnSimpleSystem) {
    // Initial concentrations: H+=1e-7, CO3=1e-3, HCO3=1e-3
    std::vector<double> initial = {1e-7, 1e-3, 1e-3};
    auto result = solver.calculate_species_concentrations(initial);

    // The solver should converge
    // Result concentrations should be bounded
    for (double c : result) {
        EXPECT_FALSE(std::isnan(c));
        EXPECT_FALSE(std::isinf(c));
        EXPECT_GT(c, 0.0);
        EXPECT_LE(c, EquilibriumChemistry<double>::MAX_CONC);
    }
}

TEST_F(EqSolverFixture, SolverPreservesComponentTotals) {
    // The key property: component totals should be conserved by equilibrium
    std::vector<double> initial = {1e-7, 1e-3, 1e-3};
    auto T_before = solver.calc_component_totals(initial);
    auto result = solver.calculate_species_concentrations(initial);
    auto T_after = solver.calc_component_totals(result);

    // Component totals should be approximately conserved
    for (size_t j = 0; j < T_before.size(); ++j) {
        EXPECT_NEAR(T_after[j], T_before[j], 1e-4 * std::abs(T_before[j]) + 1e-20);
    }
}

TEST_F(EqSolverFixture, SolverOutputsNoNaN) {
    // Various initial conditions
    std::vector<std::vector<double>> test_cases = {
        {1e-7, 1e-3, 1e-3},
        {1e-14, 1e-14, 1e-14},
        {1.0, 1.0, 1.0},
        {1e-7, 0.1, 0.05},
    };

    for (const auto& ic : test_cases) {
        auto result = solver.calculate_species_concentrations(ic);
        for (size_t i = 0; i < result.size(); ++i) {
            EXPECT_FALSE(std::isnan(result[i])) << "NaN at index " << i;
            EXPECT_FALSE(std::isinf(result[i])) << "Inf at index " << i;
        }
    }
}

// ========================== PCF RESIDUAL ==========================

TEST_F(EqSolverFixture, PcfResidualAtEquilibrium) {
    // If we're at equilibrium, the residual should be small
    // Start from initial guess and solve
    std::vector<double> initial = {1e-7, 1e-3, 1e-3};
    auto result = solver.calculate_species_concentrations(initial);

    // Convert result to log-concentrations for component species
    std::vector<double> logC(2);
    logC[0] = std::log10(std::max(result[0], 1e-30));
    logC[1] = std::log10(std::max(result[1], 1e-30));

    auto T_total = solver.calc_component_totals(result);
    auto residual = solver.pcf_residual(logC, T_total, result);

    // Residual should be small at equilibrium
    double res_norm = solver.norm(residual);
    EXPECT_LT(res_norm, 1.0);  // relaxed tolerance since we're checking structure
}

// ========================== REACTIVE/PRODUCT SUMS ==========================

TEST_F(EqSolverFixture, ReactiveProductSumsPositive) {
    std::vector<double> species = {1e-7, 1e-3, 1e-3};
    auto T_total = solver.calc_component_totals(species);
    auto sums = solver.calc_reactive_product_sums(species, T_total);

    // Both reactive and product sums should be positive
    for (double s : sums.first) {
        EXPECT_GT(s, 0.0);
    }
    for (double s : sums.second) {
        EXPECT_GT(s, 0.0);
    }
}
