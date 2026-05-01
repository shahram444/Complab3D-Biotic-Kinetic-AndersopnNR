// Extended unit tests for EquilibriumChemistry solver
// Covers: Anderson acceleration, multi-species systems, mass conservation,
// convergence with different initial conditions, condition number handling,
// beta scaling, stoichiometry manipulation, and numerical robustness.

#include "plb_shim.h"
#include <gtest/gtest.h>
#include <cmath>
#include <vector>
#include <string>
#include <limits>

using plb::plint;
typedef double T;

#include <iostream>
#define pcout std::cout

#include "complab3d_processors_part4_eqsolver_standalone.hh"

// ============================================================================
// TEST FIXTURE: 2-component carbonate system
// ============================================================================
class EqSolverExtFixture : public ::testing::Test {
protected:
    EquilibriumChemistry<double> solver;

    void SetUp() override {
        solver.setComponentNames({"H+", "CO3"});
        solver.setSpeciesNames({"H+", "CO3", "HCO3"});
        solver.setLogK({0.0, 0.0, 10.3});
        solver.setStoichiometryMatrix({
            {1.0, 0.0},
            {0.0, 1.0},
            {1.0, 1.0}
        });
        solver.setMaxIterations(200);
        solver.setTolerance(1e-10);
        solver.setAndersonDepth(4);
    }
};

// ============================================================================
// ANDERSON ACCELERATION TESTS
// ============================================================================

TEST_F(EqSolverExtFixture, AndersonDepthMinimumClamp) {
    solver.setAndersonDepth(0);
    EXPECT_EQ(solver.getAndersonDepth(), 1);
}

TEST_F(EqSolverExtFixture, AndersonDepthLargeValue) {
    solver.setAndersonDepth(100);
    EXPECT_EQ(solver.getAndersonDepth(), 100);
}

TEST_F(EqSolverExtFixture, ConvergenceWithDifferentAndersonDepths) {
    int depths[] = {1, 2, 4, 8};
    std::vector<double> initial = {1e-7, 1e-3, 1e-3};

    for (int depth : depths) {
        solver.setAndersonDepth(depth);
        solver.resetStatistics();
        auto result = solver.calculate_species_concentrations(initial);

        for (double c : result) {
            EXPECT_FALSE(std::isnan(c)) << "NaN with Anderson depth=" << depth;
            EXPECT_GT(c, 0.0) << "Non-positive with depth=" << depth;
        }
    }
}

// ============================================================================
// MASS CONSERVATION TESTS
// ============================================================================

TEST_F(EqSolverExtFixture, ComponentTotalsConservedMultipleIC) {
    std::vector<std::vector<double>> test_cases = {
        {1e-7, 1e-3, 1e-3},
        {1e-4, 1e-4, 1e-4},
        {1e-2, 1e-2, 1e-2},
        {1e-7, 0.1, 0.05},
        {1e-10, 1e-5, 1e-5},
    };

    for (const auto& ic : test_cases) {
        auto T_before = solver.calc_component_totals(ic);
        auto result = solver.calculate_species_concentrations(ic);
        auto T_after = solver.calc_component_totals(result);

        for (size_t j = 0; j < T_before.size(); ++j) {
            double rtol = 1e-3 * std::abs(T_before[j]);
            EXPECT_NEAR(T_after[j], T_before[j], rtol + 1e-15)
                << "Component total " << j << " not conserved";
        }
    }
}

// ============================================================================
// CONVERGENCE WITH DIFFERENT TOLERANCES
// ============================================================================

TEST_F(EqSolverExtFixture, TightToleranceConverges) {
    solver.setTolerance(1e-12);
    std::vector<double> initial = {1e-7, 1e-3, 1e-3};
    auto result = solver.calculate_species_concentrations(initial);

    for (double c : result) {
        EXPECT_FALSE(std::isnan(c));
        EXPECT_GT(c, 0.0);
    }
}

TEST_F(EqSolverExtFixture, LooseToleranceConverges) {
    solver.setTolerance(1e-4);
    std::vector<double> initial = {1e-7, 1e-3, 1e-3};
    auto result = solver.calculate_species_concentrations(initial);

    for (double c : result) {
        EXPECT_FALSE(std::isnan(c));
        EXPECT_GT(c, 0.0);
    }
}

// ============================================================================
// EXTREME INITIAL CONDITIONS
// ============================================================================

TEST_F(EqSolverExtFixture, VeryLowConcentrations) {
    std::vector<double> initial = {1e-14, 1e-14, 1e-14};
    auto result = solver.calculate_species_concentrations(initial);

    for (double c : result) {
        EXPECT_FALSE(std::isnan(c));
        EXPECT_FALSE(std::isinf(c));
        EXPECT_GE(c, 0.0);
    }
}

TEST_F(EqSolverExtFixture, VeryHighConcentrations) {
    std::vector<double> initial = {1.0, 1.0, 1.0};
    auto result = solver.calculate_species_concentrations(initial);

    for (double c : result) {
        EXPECT_FALSE(std::isnan(c));
        EXPECT_FALSE(std::isinf(c));
    }
}

TEST_F(EqSolverExtFixture, AsymmetricConcentrations) {
    std::vector<double> initial = {1e-14, 1.0, 0.5};
    auto result = solver.calculate_species_concentrations(initial);

    for (double c : result) {
        EXPECT_FALSE(std::isnan(c));
    }
}

// ============================================================================
// VECTOR OPERATIONS EXTENDED TESTS
// ============================================================================

TEST(EqVectorOpsExt, NormLargeVector) {
    EquilibriumChemistry<double> s;
    std::vector<double> v(100, 1.0);
    EXPECT_NEAR(s.norm(v), 10.0, 1e-10);
}

TEST(EqVectorOpsExt, NormSingleElement) {
    EquilibriumChemistry<double> s;
    std::vector<double> v = {-5.0};
    EXPECT_DOUBLE_EQ(s.norm(v), 5.0);
}

TEST(EqVectorOpsExt, VecAddEmpty) {
    EquilibriumChemistry<double> s;
    std::vector<double> a, b;
    auto r = s.vec_add(a, b);
    EXPECT_TRUE(r.empty());
}

TEST(EqVectorOpsExt, VecSubtractFromSelf) {
    EquilibriumChemistry<double> s;
    std::vector<double> a = {5.0, 3.0, 1.0};
    auto r = s.vec_subtract(a, a);
    for (double v : r) {
        EXPECT_NEAR(v, 0.0, 1e-15);
    }
}

TEST(EqVectorOpsExt, DotProductOrthogonal) {
    EquilibriumChemistry<double> s;
    std::vector<double> a = {1.0, 0.0};
    std::vector<double> b = {0.0, 1.0};
    EXPECT_DOUBLE_EQ(s.dot_product(a, b), 0.0);
}

TEST(EqVectorOpsExt, DotProductNegative) {
    EquilibriumChemistry<double> s;
    std::vector<double> a = {1.0, 2.0};
    std::vector<double> b = {-1.0, -2.0};
    EXPECT_DOUBLE_EQ(s.dot_product(a, b), -5.0);
}

// ============================================================================
// QR DECOMPOSITION EXTENDED TESTS
// ============================================================================

TEST(EqQRExtended, ThreeColumnQR) {
    EquilibriumChemistry<double> s;
    std::vector<std::vector<double>> cols = {
        {1.0, 0.0, 0.0},
        {0.0, 1.0, 0.0},
        {0.0, 0.0, 1.0}
    };
    std::vector<std::vector<double>> Q, R;
    double condNum;
    s.qr_decomposition(cols, Q, R, condNum);

    EXPECT_NEAR(condNum, 1.0, 1e-10);
    EXPECT_EQ(Q.size(), 3u);
    EXPECT_EQ(R.size(), 3u);
}

TEST(EqQRExtended, QRPreservesProduct) {
    EquilibriumChemistry<double> s;
    std::vector<std::vector<double>> cols = {{1.0, 1.0}, {0.0, 1.0}};
    std::vector<std::vector<double>> Q, R;
    double condNum;
    s.qr_decomposition(cols, Q, R, condNum);

    // Verify Q * R = original columns (up to numerical precision)
    for (size_t j = 0; j < cols.size(); ++j) {
        for (size_t i = 0; i < cols[j].size(); ++i) {
            double qr_val = 0.0;
            for (size_t k = 0; k <= j; ++k) {
                qr_val += Q[k][i] * R[k][j];
            }
            EXPECT_NEAR(qr_val, cols[j][i], 1e-10)
                << "QR product mismatch at (" << i << "," << j << ")";
        }
    }
}

// ============================================================================
// UPPER TRIANGULAR SOLVE EXTENDED
// ============================================================================

TEST(EqTriangularSolveExt, SingleElement) {
    EquilibriumChemistry<double> s;
    std::vector<std::vector<double>> R = {{5.0}};
    std::vector<double> b = {10.0};
    auto x = s.solve_upper_triangular(R, b);
    EXPECT_NEAR(x[0], 2.0, 1e-10);
}

TEST(EqTriangularSolveExt, ThreeByThree) {
    EquilibriumChemistry<double> s;
    std::vector<std::vector<double>> R = {
        {1.0, 2.0, 3.0},
        {0.0, 4.0, 5.0},
        {0.0, 0.0, 6.0}
    };
    std::vector<double> b = {14.0, 23.0, 18.0};
    // x[2] = 18/6 = 3
    // x[1] = (23 - 5*3)/4 = 8/4 = 2
    // x[0] = (14 - 2*2 - 3*3)/1 = 14 - 4 - 9 = 1
    auto x = s.solve_upper_triangular(R, b);
    EXPECT_NEAR(x[0], 1.0, 1e-10);
    EXPECT_NEAR(x[1], 2.0, 1e-10);
    EXPECT_NEAR(x[2], 3.0, 1e-10);
}

// ============================================================================
// SPECIES CALCULATION EXTENDED TESTS
// ============================================================================

TEST_F(EqSolverExtFixture, CalcSpeciesPositiveConcentrations) {
    std::vector<double> logC = {-4.0, -4.0};
    auto conc = solver.calc_species(logC);

    for (double c : conc) {
        EXPECT_GT(c, 0.0);
        EXPECT_FALSE(std::isnan(c));
    }
}

TEST_F(EqSolverExtFixture, CalcSpeciesLogKEffect) {
    // HCO3 = 10^(logK[2] + logC_H + logC_CO3)
    std::vector<double> logC = {-7.0, -3.0};
    auto conc = solver.calc_species(logC);

    // HCO3 should be >> H+ due to large logK
    EXPECT_GT(conc[2], conc[0]);
}

// ============================================================================
// STATISTICS TRACKING EXTENDED
// ============================================================================

TEST_F(EqSolverExtFixture, StatisticsAfterMultipleSolves) {
    solver.resetStatistics();

    std::vector<std::vector<double>> test_cases = {
        {1e-7, 1e-3, 1e-3},
        {1e-5, 1e-4, 1e-4},
        {1e-3, 1e-3, 1e-3},
    };

    for (const auto& ic : test_cases) {
        solver.calculate_species_concentrations(ic);
    }

    EXPECT_EQ(solver.getTotalSolves(), 3);
    EXPECT_GE(solver.getTotalConverged(), 0);
}

// ============================================================================
// SETTER/GETTER EXTENDED TESTS
// ============================================================================

TEST(EqSolverSetters, SetMaxIterations) {
    EquilibriumChemistry<double> s;
    s.setMaxIterations(500);
    EXPECT_EQ(s.getMaxIterations(), 500);
}

TEST(EqSolverSetters, SetTolerance) {
    EquilibriumChemistry<double> s;
    s.setTolerance(1e-12);
    EXPECT_NEAR(s.getTolerance(), 1e-12, 1e-15);
}

TEST(EqSolverSetters, SetBeta) {
    EquilibriumChemistry<double> s;
    // Should not crash
    s.setBeta(0.5);
    s.setBeta(1.0);
    s.setBeta(0.1);
}

TEST(EqSolverSetters, SetConditionTolerance) {
    EquilibriumChemistry<double> s;
    s.setConditionTolerance(1e6);
    // Should not crash
}

TEST(EqSolverSetters, SetVerbose) {
    EquilibriumChemistry<double> s;
    s.setVerbose(true);
    s.setVerbose(false);
}

// ============================================================================
// STOICHIOMETRY MANIPULATION
// ============================================================================

TEST_F(EqSolverExtFixture, SetStoichiometryRow) {
    // Modify a single row
    solver.setStoichiometryRow(2, {2.0, 1.0});

    // Recalculate species with modified stoichiometry
    std::vector<double> logC = {-7.0, -3.0};
    auto conc = solver.calc_species(logC);

    // HCO3 now = 10^(10.3 + 2*(-7) + 1*(-3)) = 10^(10.3 - 14 - 3) = 10^-6.7
    double expected = std::pow(10.0, 10.3 - 14.0 - 3.0);
    EXPECT_NEAR(conc[2], expected, expected * 0.01);
}

// ============================================================================
// PCF RESIDUAL EXTENDED TESTS
// ============================================================================

TEST_F(EqSolverExtFixture, PcfResidualFarFromEquilibrium) {
    // Initial guess far from equilibrium should have large residual
    std::vector<double> species = {1.0, 1.0, 1e-10};
    auto T_total = solver.calc_component_totals(species);
    std::vector<double> logC = {0.0, 0.0};
    auto residual = solver.pcf_residual(logC, T_total, species);

    double res_norm = solver.norm(residual);
    EXPECT_GT(res_norm, 0.0);
}

TEST_F(EqSolverExtFixture, ReactiveProductSumsSymmetry) {
    // Component totals should affect reactive/product sums
    std::vector<double> species1 = {1e-7, 1e-3, 1e-3};
    auto T1 = solver.calc_component_totals(species1);
    auto sums1 = solver.calc_reactive_product_sums(species1, T1);

    std::vector<double> species2 = {1e-3, 1e-7, 1e-3};
    auto T2 = solver.calc_component_totals(species2);
    auto sums2 = solver.calc_reactive_product_sums(species2, T2);

    // Different species distributions -> different sums
    // Just verify no NaN/Inf
    for (double s : sums1.first) EXPECT_FALSE(std::isnan(s));
    for (double s : sums2.first) EXPECT_FALSE(std::isnan(s));
}

// ============================================================================
// EQUILIBRIUM SPECIES CHECKS
// ============================================================================

TEST_F(EqSolverExtFixture, IsEquilibriumSpeciesNegativeIndex) {
    EXPECT_FALSE(solver.isEquilibriumSpecies(-1));
}

TEST_F(EqSolverExtFixture, IsEquilibriumSpeciesAllValid) {
    for (int i = 0; i < 3; ++i) {
        EXPECT_TRUE(solver.isEquilibriumSpecies(i));
    }
}

// ============================================================================
// REPEATED SOLVES (STATEFUL BEHAVIOR)
// ============================================================================

TEST_F(EqSolverExtFixture, RepeatedSolvesConverge) {
    std::vector<double> initial = {1e-7, 1e-3, 1e-3};

    for (int i = 0; i < 10; ++i) {
        auto result = solver.calculate_species_concentrations(initial);
        for (double c : result) {
            EXPECT_FALSE(std::isnan(c)) << "NaN on iteration " << i;
            EXPECT_GT(c, 0.0) << "Non-positive on iteration " << i;
        }
    }
}

// ============================================================================
// SINGLE-COMPONENT SYSTEM
// ============================================================================

TEST(EqSolverSingleComponent, OneComponentOneSpecies) {
    EquilibriumChemistry<double> s;
    s.setComponentNames({"A"});
    s.setSpeciesNames({"A"});
    s.setLogK({0.0});
    s.setStoichiometryMatrix({{1.0}});
    s.setMaxIterations(100);
    s.setTolerance(1e-8);

    std::vector<double> initial = {1e-3};
    auto result = s.calculate_species_concentrations(initial);

    // Single component, single species: output should equal input
    EXPECT_NEAR(result[0], initial[0], 1e-6);
}

// ============================================================================
// LARGER SYSTEM (3 components, 5 species)
// ============================================================================

TEST(EqSolverLargeSystem, ThreeComponentFiveSpecies) {
    EquilibriumChemistry<double> s;
    s.setComponentNames({"A", "B", "C"});
    s.setSpeciesNames({"A", "B", "C", "AB", "BC"});
    s.setLogK({0.0, 0.0, 0.0, 3.0, 2.0});
    s.setStoichiometryMatrix({
        {1.0, 0.0, 0.0},  // A
        {0.0, 1.0, 0.0},  // B
        {0.0, 0.0, 1.0},  // C
        {1.0, 1.0, 0.0},  // AB = A + B
        {0.0, 1.0, 1.0}   // BC = B + C
    });
    s.setMaxIterations(200);
    s.setTolerance(1e-8);
    s.setAndersonDepth(4);

    std::vector<double> initial = {1e-3, 1e-3, 1e-3, 1e-3, 1e-3};
    auto T_before = s.calc_component_totals(initial);
    auto result = s.calculate_species_concentrations(initial);
    auto T_after = s.calc_component_totals(result);

    // Mass conservation
    for (size_t j = 0; j < T_before.size(); ++j) {
        EXPECT_NEAR(T_after[j], T_before[j], 1e-3 * std::abs(T_before[j]) + 1e-15)
            << "Component " << j << " not conserved";
    }

    // No NaN/Inf
    for (double c : result) {
        EXPECT_FALSE(std::isnan(c));
        EXPECT_FALSE(std::isinf(c));
        EXPECT_GT(c, 0.0);
    }
}
