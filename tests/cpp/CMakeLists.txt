cmake_minimum_required(VERSION 3.14)
project(complab_tests CXX)

set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# ---- GoogleTest via FetchContent ----
include(FetchContent)
FetchContent_Declare(
  googletest
  GIT_REPOSITORY https://github.com/google/googletest.git
  GIT_TAG        v1.14.0
)
set(gtest_force_shared_crt ON CACHE BOOL "" FORCE)
FetchContent_MakeAvailable(googletest)

enable_testing()
include(GoogleTest)

# ---- Project paths ----
set(PROJECT_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/../..")

# ---- Test: Stability Checks ----
add_executable(test_stability test_stability.cpp)
target_include_directories(test_stability PRIVATE "${PROJECT_ROOT}/src")
target_link_libraries(test_stability GTest::gtest_main)
gtest_discover_tests(test_stability)

# ---- Test: Abiotic Kinetics ----
add_executable(test_abiotic_kinetics test_abiotic_kinetics.cpp)
target_include_directories(test_abiotic_kinetics PRIVATE "${PROJECT_ROOT}")
target_link_libraries(test_abiotic_kinetics GTest::gtest_main)
gtest_discover_tests(test_abiotic_kinetics)

# ---- Test: Biotic Kinetics (Biofilm) ----
add_executable(test_biotic_kinetics test_biotic_kinetics.cpp)
target_include_directories(test_biotic_kinetics PRIVATE "${PROJECT_ROOT}")
target_link_libraries(test_biotic_kinetics GTest::gtest_main)
gtest_discover_tests(test_biotic_kinetics)

# ---- Test: Planktonic Kinetics ----
add_executable(test_planktonic_kinetics test_planktonic_kinetics.cpp)
target_include_directories(test_planktonic_kinetics PRIVATE "${PROJECT_ROOT}")
target_link_libraries(test_planktonic_kinetics GTest::gtest_main)
gtest_discover_tests(test_planktonic_kinetics)

# ---- Test: Equilibrium Solver (Anderson + PCF) ----
add_executable(test_eq_solver test_eq_solver.cpp)
target_include_directories(test_eq_solver PRIVATE
    "${CMAKE_CURRENT_SOURCE_DIR}"
    "${PROJECT_ROOT}/src"
)
target_link_libraries(test_eq_solver GTest::gtest_main)
gtest_discover_tests(test_eq_solver)

# ---- Test: Diagnostics and Mass Balance ----
add_executable(test_diagnostics test_diagnostics.cpp)
target_include_directories(test_diagnostics PRIVATE "${PROJECT_ROOT}")
target_link_libraries(test_diagnostics GTest::gtest_main)
gtest_discover_tests(test_diagnostics)

# ---- Test: LBM Utilities (D3Q7, FD Laplacian, Flow Math) ----
add_executable(test_lbm_utils test_lbm_utils.cpp)
target_include_directories(test_lbm_utils PRIVATE "${PROJECT_ROOT}")
target_link_libraries(test_lbm_utils GTest::gtest_main)
gtest_discover_tests(test_lbm_utils)

# ======== Extended Test Suites ========

# ---- Test: Stability Checks Extended ----
add_executable(test_stability_extended test_stability_extended.cpp)
target_include_directories(test_stability_extended PRIVATE "${PROJECT_ROOT}/src")
target_link_libraries(test_stability_extended GTest::gtest_main)
gtest_discover_tests(test_stability_extended)

# ---- Test: Biotic Kinetics Extended ----
add_executable(test_biotic_kinetics_extended test_biotic_kinetics_extended.cpp)
target_include_directories(test_biotic_kinetics_extended PRIVATE "${PROJECT_ROOT}")
target_link_libraries(test_biotic_kinetics_extended GTest::gtest_main)
gtest_discover_tests(test_biotic_kinetics_extended)

# ---- Test: Abiotic Kinetics Extended ----
add_executable(test_abiotic_kinetics_extended test_abiotic_kinetics_extended.cpp)
target_include_directories(test_abiotic_kinetics_extended PRIVATE "${PROJECT_ROOT}")
target_link_libraries(test_abiotic_kinetics_extended GTest::gtest_main)
gtest_discover_tests(test_abiotic_kinetics_extended)

# ---- Test: Planktonic Kinetics Extended ----
add_executable(test_planktonic_kinetics_extended test_planktonic_kinetics_extended.cpp)
target_include_directories(test_planktonic_kinetics_extended PRIVATE "${PROJECT_ROOT}")
target_link_libraries(test_planktonic_kinetics_extended GTest::gtest_main)
gtest_discover_tests(test_planktonic_kinetics_extended)

# ---- Test: Equilibrium Solver Extended ----
add_executable(test_eq_solver_extended test_eq_solver_extended.cpp)
target_include_directories(test_eq_solver_extended PRIVATE
    "${CMAKE_CURRENT_SOURCE_DIR}"
    "${PROJECT_ROOT}/src"
)
target_link_libraries(test_eq_solver_extended GTest::gtest_main)
gtest_discover_tests(test_eq_solver_extended)

# ---- Test: LBM Utilities Extended ----
add_executable(test_lbm_utils_extended test_lbm_utils_extended.cpp)
target_include_directories(test_lbm_utils_extended PRIVATE "${PROJECT_ROOT}")
target_link_libraries(test_lbm_utils_extended GTest::gtest_main)
gtest_discover_tests(test_lbm_utils_extended)

# ======== New Test Suites (Coverage Gaps) ========

# ---- Test: Boundary Conditions (Dirichlet / Neumann / Periodic) ----
add_executable(test_bc test_bc.cpp)
target_include_directories(test_bc PRIVATE
    "${CMAKE_CURRENT_SOURCE_DIR}"
    "${PROJECT_ROOT}"
)
target_link_libraries(test_bc GTest::gtest_main)
gtest_discover_tests(test_bc)

# ---- Test: Growth Integration (time-stepping, sessile vs planktonic) ----
add_executable(test_growth_integration test_growth_integration.cpp)
target_include_directories(test_growth_integration PRIVATE "${PROJECT_ROOT}")
target_link_libraries(test_growth_integration GTest::gtest_main)
gtest_discover_tests(test_growth_integration)

# ---- Test: Diffusion Physics (tortuosity, analytical, Peclet) ----
add_executable(test_diffusion_bc test_diffusion_bc.cpp)
target_include_directories(test_diffusion_bc PRIVATE
    "${CMAKE_CURRENT_SOURCE_DIR}"
    "${PROJECT_ROOT}"
)
target_link_libraries(test_diffusion_bc GTest::gtest_main)
gtest_discover_tests(test_diffusion_bc)

# ---- Test: Coupled Reaction-Transport (Damkohler, Thiele, breakthrough) ----
add_executable(test_reaction_transport test_reaction_transport.cpp)
target_include_directories(test_reaction_transport PRIVATE "${PROJECT_ROOT}")
target_link_libraries(test_reaction_transport GTest::gtest_main)
gtest_discover_tests(test_reaction_transport)
