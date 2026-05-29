add_library(usermod_game INTERFACE)

target_sources(usermod_game INTERFACE
    ${CMAKE_CURRENT_LIST_DIR}/modgame.c
    ${CMAKE_CURRENT_LIST_DIR}/engine.cpp
    ${CMAKE_CURRENT_LIST_DIR}/ili9341.cpp
)

target_include_directories(usermod_game INTERFACE
    ${CMAKE_CURRENT_LIST_DIR}
)

target_link_libraries(usermod_game INTERFACE
    pico_stdlib
    hardware_adc
    hardware_clocks
    hardware_spi
)

target_compile_features(usermod_game INTERFACE
    cxx_std_17
)

target_link_libraries(usermod INTERFACE usermod_game)
