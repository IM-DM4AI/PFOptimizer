cmake_minimum_required(VERSION 2.8.12...3.29)
project(example_cpp)

set(CMAKE_CXX_STANDARD 17)

find_package(PythonLibs)

add_executable(example cpp_import_example.cpp)
add_executable(basic cpp_basic_example.cpp)

target_include_directories(example PRIVATE ${PYTHON_INCLUDE_DIRS})
target_link_libraries(example ${PYTHON_LIBRARIES})

target_include_directories(basic PRIVATE ${PYTHON_INCLUDE_DIRS})
target_link_libraries(basic ${PYTHON_LIBRARIES})