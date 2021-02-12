#!/bin/zsh -fx

GIT_REPOS_ROOT=/usr/local/repos/git
EIEIO_ROOT=${GIT_REPOS_ROOT}/eieio
COLOUR_ROOT=${GIT_REPOS_ROOT}/colour-science/colour
ACTIVE_PYTHON_PATH=$(which python)
ACTIVE_PYTHON_MAJOR_MINOR=${ACTIVE_PYTHON_PATH:h:h:t:r} #yow
ACTIVE_PYTHON_LIB_DIR=${ACTIVE_PYTHON_PATH:h:h}/lib
# ACTIVE_HOST_SITE_PACKAGE_DIR=${ACTIVE_PYTHON_LIB_DIR}/python${ACTIVE_PYTHON_MAJOR_MINOR}/site-packages
# PYTHONPATH=${EIEIO_ROOT}:${COLOUR_ROOT}:${ACTIVE_HOST_SITE_PACKAGE_DIR}
export PYTHONPATH=${EIEIO_ROOT}:${COLOUR_ROOT}

python -m eieio.cli_tools.measure \
    --device i1Pro \
    --output_dir /tmp \
    --base_measurement_name foo \
    --mode emissive \
    --sequence_file "${0:h}"/just_calibration.sis \
    --verbose
