#!/bin/bash

# From a clean ubuntu-minimal image, install what is needed to run a simulation
# script directly on the image.
# While the simulation script is stored alongside this bootstrap script in the
# repository, the bootsrap script is assumed to be used on its own.

set -eo pipefail

NARUPA_PORT=38801
MINICONDA_PATH="$HOME/miniconda"
NARUPA_ARTIFACT_URL="https://gitlab.com/intangiblerealities/narupa-protocol/-/jobs/492086300/artifacts/download"

# Avoid interuptions where apt ask a question.
export DEBIAN_FRONTEND=noninteractive

sudo apt update
sudo apt upgrade -y  # We are responsible for keeping the OS up to date

sudo apt-get install -y bzip2 build-essential wget git curl unzip cmake

# Install cuda from the nvidia repository
# TODO: installing the "cuda" package comes with hundreds of packages as
#       dependencies. Find the minimum package list to install.
sudo apt-get install -y software-properties-common
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu1804/x86_64/cuda-ubuntu1804.pin
sudo mv cuda-ubuntu1804.pin /etc/apt/preferences.d/cuda-repository-pin-600
sudo apt-key adv --fetch-keys https://developer.download.nvidia.com/compute/cuda/repos/ubuntu1804/x86_64/7fa2af80.pub
sudo add-apt-repository "deb http://developer.download.nvidia.com/compute/cuda/repos/ubuntu1804/x86_64/ /"
sudo apt-get update
DEBIAN_FRONTEND=noninteractive sudo apt-get -y install cuda-10-1


# We package Narupa using conda. Here we install conda.
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh
bash miniconda.sh -b -p $MINICONDA_PATH && rm miniconda.sh
PATH="${MINICONDA_PATH}/bin:$PATH"
conda init bash
source $HOME/.bashrc
conda update -y -n base -c defaults conda


# The simulation script we aim to run uses features that are not yet merged
# into master, and therefore not available on anaconda cloud. We get the conda
# packages from the CI on the feature/python-vmd-imd branch.
wget ${NARUPA_ARTIFACT_URL} -O artifacts.zip
unzip artifacts.zip
conda install -y -c omnia/label/cuda101 -c conda-forge -c ./conda-bld narupa-openmm narupa-pyvmdimd swig networkx matplotlib
# The grpcio package from conda-forge seems to have an issue with SO_REUSE_PORT.
# We overwrite the package by the one provided on pypi that does not have the
# problem.
# TODO: report the issue upstream.
pip install --ignore-installed grpcio


# Compile the vmd-imd plugin for openMM
git clone https://gitlab.com/intangiblerealities/narupaplugins/openmm-vmd-imd.git
mkdir build && cd build
cmake ../openmm-vmd-imd \
    -DOPENMM_DIR=${MINICONDA_PATH} \
    -DCMAKE_INSTALL_PREFIX=${MINICONDA_PATH} \
    -DUSE_OLD_CXX11_ABI=on \
    -DCMAKE_BUILD_TYPE=RELEASE
make && make install && make PythonInstall
cd ..


# Obtain the simulation script
# TODO: store simulation inputs and script in a file bucket so they can be
#       added and modified without the need to alter the VM image.
git clone https://gitlab.com/intangiblerealities/covid-docker.git


# Open the port for Narupa
# Note that the port must also be open in the subnet on OCI.
sudo iptables -I INPUT 1 -p tcp --dport ${NARUPA_PORT} -j ACCEPT
sudo iptables -I OUTPUT 1 -p tcp --dport ${NARUPA_PORT} -j ACCEPT
sudo bash -c "iptables-save > /etc/iptables.rules"

# Add the systemd service to begin at startup.
sudo cp covid-docker/narupa_cloud.service /etc/systemd/system
sudo chmod 644 /etc/systemd/system/narupa_cloud.service
chmod +x covid-docker/start.sh
sudo systemctl enable narupa_cloud.service

# TODO: Add some cleanup to avoid too much leftover files.