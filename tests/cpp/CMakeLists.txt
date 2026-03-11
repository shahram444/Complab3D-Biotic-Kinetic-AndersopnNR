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
    "${CMAKE_CURRENT_SOURCE_DIR}"   # for standalone header and plb_shim.h
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
