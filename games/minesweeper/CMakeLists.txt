# Minesweeper Game - CMake Configuration
# Supports both native SFML build and WebAssembly via Emscripten

cmake_minimum_required(VERSION 3.15)
project(Minesweeper VERSION 1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Source files
set(SOURCES
    src/main.cpp
)

# ============================================
# Native Build (SFML)
# ============================================
if(NOT EMSCRIPTEN)
    # Find SFML
    find_package(SFML 2.5 COMPONENTS graphics window system REQUIRED)
    
    # Create executable
    add_executable(minesweeper ${SOURCES})
    
    # Link SFML
    target_link_libraries(minesweeper 
        sfml-graphics 
        sfml-window 
        sfml-system
    )
    
    # Copy assets to build directory
    file(COPY ${CMAKE_SOURCE_DIR}/assets DESTINATION ${CMAKE_BINARY_DIR})

# ============================================
# WebAssembly Build (Emscripten)
# ============================================
else()
    # Create executable
    add_executable(minesweeper ${SOURCES})
    
    # Emscripten compiler flags
    set(EM_FLAGS 
        "-s USE_SDL=2"
        "-s WASM=1"
        "-s ALLOW_MEMORY_GROWTH=1"
        "-s NO_EXIT_RUNTIME=1"
        "-s EXPORTED_RUNTIME_METHODS=['ccall','cwrap']"
        "--preload-file ${CMAKE_SOURCE_DIR}/assets@/assets"
        "-O2"
    )
    
    # Join flags into a string
    string(JOIN " " EM_FLAGS_STR ${EM_FLAGS})
    
    # Apply flags
    set_target_properties(minesweeper PROPERTIES
        SUFFIX ".js"
        LINK_FLAGS "${EM_FLAGS_STR}"
    )
    
    # Additional Emscripten settings
    target_compile_options(minesweeper PRIVATE
        -O2
        -Wall
    )
endif()

# ============================================
# Installation
# ============================================
install(TARGETS minesweeper DESTINATION bin)
install(DIRECTORY assets DESTINATION share/minesweeper)

