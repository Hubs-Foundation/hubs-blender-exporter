cmake_minimum_required(VERSION 3.5)

project(RecastBlenderAddon LANGUAGES CXX)

set(BUILD_TEST_APP_EXE OFF CACHE BOOL "Build test app exe file")
set(BUILD_LIB ON CACHE BOOL "Build dll file")
set(RECAST_LIB "${CMAKE_CURRENT_SOURCE_DIR}/../recast/Recast/libRecast.a" CACHE PATH "Path to recast.lib file.")
set(RECAST_ROOT_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../recast" CACHE PATH "Path to recast root directory.")
set(VERBOSE_LOGS OFF CACHE BOOL "Print entry and result values of arrays")

set(CMAKE_INCLUDE_CURRENT_DIR ON)
set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

include_directories(${RECAST_ROOT_DIR}/Recast/Include)

add_definitions(-DRECASTBLENDERADDON_LIBRARY)

set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS_INIT} -fPIC")

if(VERBOSE_LOGS)
    add_definitions(-DVERBOSE_LOGS)
endif(VERBOSE_LOGS)

if(BUILD_LIB)
    add_library(RecastBlenderAddon SHARED recast-capi.cpp mesh_navmesh.cpp)
    target_link_libraries(RecastBlenderAddon ${RECAST_LIB})
endif(BUILD_LIB)
