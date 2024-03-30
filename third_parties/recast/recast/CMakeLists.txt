cmake_minimum_required(VERSION 3.0)

set(CMAKE_OSX_ARCHITECTURES "arm64;x86_64" CACHE STRING "" FORCE)

project(RecastNavigation)

# lib versions
SET(SOVERSION 1)
SET(VERSION 1.0.0)

option(RECASTNAVIGATION_STATIC "Build static libraries" ON)

add_subdirectory(Recast)

