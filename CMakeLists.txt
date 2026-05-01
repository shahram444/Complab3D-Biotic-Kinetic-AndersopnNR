cmake_minimum_required(VERSION 3.5)

#set the project name
project(complab)
enable_language(CXX)

set(EXECUTABLE_NAME "complab")
set (CMAKE_RUNTIME_OUTPUT_DIRECTORY "../")

#if(NOT CMAKE_BUILD_TYPE)
    #set(CMAKE_BUILD_TYPE "Release")
    #set(CMAKE_CONFIGURATION_TYPES "Debug;Release")
#endif()




if(NOT CMAKE_BUILD_TYPE)
    #set(CMAKE_BUILD_TYPE "Debug")
    set(CMAKE_BUILD_TYPE "Release")
endif()



message("Generated with config types: ${CMAKE_CONFIGURATION_TYPES}")
message(${CMAKE_BUILD_TYPE})

# Compiler flags
# Append flags: set(CMAKE_XXX_FLAGS "${CMAKE_XXX_FLAGS} ...")
if(${CMAKE_CXX_COMPILER_ID} STREQUAL GNU)
    message("GCC.")
    set(CMAKE_CXX_FLAGS "-std=c++11 -Wall -Wnon-virtual-dtor")
    set(CMAKE_CXX_FLAGS_RELEASE "-O3 -DNDEBUG")
    set(CMAKE_CXX_FLAGS_DEBUG "-g -DPLB_DEBUG -O0")
elseif(${CMAKE_CXX_COMPILER_ID} STREQUAL Clang)
    message("Clang.")
    set(CMAKE_CXX_FLAGS "-std=c++11 -Wall -Wnon-virtual-dtor")
    set(CMAKE_CXX_FLAGS_RELEASE "-O3 -DNDEBUG")
    set(CMAKE_CXX_FLAGS_DEBUG "-g -DPLB_DEBUG -O0 -faddress-sanitizer -O1 -fno-omit-frame-pointer")
elseif(${CMAKE_CXX_COMPILER_ID} STREQUAL MSVC)
    message("MSVC.")
    set(CMAKE_CXX_FLAGS_RELEASE "/Ox /Ot /GS- /GL /DNDEBUG")
    set(CMAKE_CXX_FLAGS_DEBUG "/DPLB_DEBUG")
    set(CMAKE_EXE_LINKER_FLAGS_RELEASE "/LTCG /INCREMENTAL:NO /OPT:REF")
else()
    message( FATAL_ERROR "CXX compiler not recognized. CMake will quit." )
endif()

option(ENABLE_MPI "Enable MPI" ON)
if(ENABLE_MPI)
    message("Enabling MPI")
    find_package(MPI REQUIRED)
    if(MPI_CXX_FOUND)
        #set(CMAKE_CXX_COMPILER "${MPI_CXX_COMPILER}")
        include_directories(${MPI_CXX_INCLUDE_PATH})
        set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} ${MPI_CXX_COMPILE_FLAGS}")
        add_definitions(-DPLB_MPI_PARALLEL)
    endif()
endif()

if(WIN32)
    option(ENABLE_POSIX "Enable POSIX" OFF)
else()
    option(ENABLE_POSIX "Enable POSIX" ON)
endif()

if(ENABLE_POSIX)
    message("Enabling POSIX")
    add_definitions(-DPLB_USE_POSIX)
endif()

if(APPLE)
    add_definitions(-DPLB_MAC_OS_X)
endif()

if(WIN32 OR CYGWIN)
    add_definitions(-DPLB_WINDOWS)
endif()
###############################################################################
# Palabos Library — bundled at ComapLB3D/versionControl/palabos-v2.3.0/
# Paths are relative to this CMakeLists.txt so the build works on any machine
# without modification (Linux, macOS, Windows).
###############################################################################

set(PALABOS_DIR "${CMAKE_CURRENT_SOURCE_DIR}/versionControl/palabos-v2.3.0")

if(NOT EXISTS "${PALABOS_DIR}/src")
    message(FATAL_ERROR
        "Palabos source not found at:\n  ${PALABOS_DIR}/src\n"
        "Make sure the versionControl/palabos-v2.3.0/ folder is present "
        "in the JOSS_Submit directory.")
endif()

include_directories("${PALABOS_DIR}/src")
include_directories("${PALABOS_DIR}/externalLibraries")
include_directories("${PALABOS_DIR}/externalLibraries/Eigen3")

file(GLOB_RECURSE PALABOS_SRC "${PALABOS_DIR}/src/*.cpp")
file(GLOB_RECURSE EXT_SRC     "${PALABOS_DIR}/externalLibraries/tinyxml/*.cpp")

add_library(palabos STATIC ${PALABOS_SRC} ${EXT_SRC})


###############################################################################

add_executable(${EXECUTABLE_NAME} "./src/${EXECUTABLE_NAME}.cpp")

# Link with the following libraries
target_link_libraries(${EXECUTABLE_NAME} palabos)
#target_link_libraries(${EXECUTABLE_NAME} glpk)
#target_link_libraries(${EXECUTABLE_NAME} python3.6m)

if(ENABLE_MPI)
    target_link_libraries(${EXECUTABLE_NAME} ${MPI_CXX_LIBRARIES})
endif()
