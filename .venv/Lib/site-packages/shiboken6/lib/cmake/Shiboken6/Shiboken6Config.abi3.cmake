#  SHIBOKEN_BUILD_TYPE         - Tells if Shiboken was compiled in Release or Debug mode.
#  SHIBOKEN_PYTHON_INTERPRETER - Python interpreter (regular or debug) to be used with the bindings.


####### Expanded from @PACKAGE_INIT@ by configure_package_config_file() #######
####### Any changes to this file will be overwritten by the next CMake run ####
####### The input file was Shiboken6Config-spec.cmake.in                            ########

get_filename_component(PACKAGE_PREFIX_DIR "${CMAKE_CURRENT_LIST_DIR}/../../../" ABSOLUTE)

macro(set_and_check _var _file)
  set(${_var} "${_file}")
  if(NOT EXISTS "${_file}")
    message(FATAL_ERROR "File or directory ${_file} referenced by variable ${_var} does not exist !")
  endif()
endmacro()

macro(check_required_components _NAME)
  foreach(comp ${${_NAME}_FIND_COMPONENTS})
    if(NOT ${_NAME}_${comp}_FOUND)
      if(${_NAME}_FIND_REQUIRED_${comp})
        set(${_NAME}_FOUND FALSE)
      endif()
    endif()
  endforeach()
endmacro()

####################################################################################

# This is the version of Python against which Shiboken was built. Not necessarily the version
# against which a downstream project is built (e.g. PySide6).
set(SHIBOKEN_PYTHON_VERSION_MAJOR "3")
set(SHIBOKEN_PYTHON_VERSION_MINOR "10")
set(SHIBOKEN_PYTHON_VERSION_PATCH "0")
set(SHIBOKEN_PYTHON_LIMITED_API "1")

# Import targets and call variable set up functions  only when using an installed shiboken config
# file (so not during a regular shiboken build, or during a super project build).
if (NOT TARGET Shiboken6::libshiboken)
    include("${CMAKE_CURRENT_LIST_DIR}/Shiboken6Targets.cmake")
    include("${CMAKE_CURRENT_LIST_DIR}/ShibokenHelpers.cmake")

    # Compute the python include and libraries path if needed (aka not part of super project build).
    shiboken_find_required_python(3)
    shiboken_check_if_built_and_target_python_are_compatible()
    shiboken_check_if_limited_api()
    shiboken_compute_python_includes(IS_CALLED_FROM_EXPORT)
    shiboken_compute_python_libraries(IS_CALLED_FROM_EXPORT)
endif()

# Get the "python interpreter" dynamic global property as a variable instead. It brings it into
# scope for super project builds.
get_property(SHIBOKEN_PYTHON_INTERPRETER GLOBAL PROPERTY SHIBOKEN_PYTHON_INTERPRETER)

# Set static variables.
set(SHIBOKEN_PYTHON_EXTENSION_SUFFIX "")
set(SHIBOKEN_PYTHON_SHARED_LIBRARY_SUFFIX ".abi3")
set(SHIBOKEN_PYTHON_CONFIG_SUFFIX ".abi3")
set(SHIBOKEN_SO_VERSION "6.11")
set(SHIBOKEN_BUILD_TYPE "Release")

message(STATUS "libshiboken built for Release")
