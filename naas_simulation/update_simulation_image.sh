#!/bin/bash
set -e
cd /

sudo apt-get update
sudo apt-get upgrade -y
sudo DEBIAN_FRONTEND=noninteractive apt-get -y install git software-properties-common wget

DISTRO='ubuntu2004'
VERSION='1804'
ARCHITECTURE='x84_64'
#sudo dpkg -i cuda-repo-${DISTRO}_${VERSION}_${ARCHITECTURE}.deb
#sudo add-apt-repository "deb https://developer.download.nvidia.com/compute/cuda/repos/${DISTRO}/${ARCHITECTURE}/ /"
#sudo apt-key add /var/cuda-repo-${DISTRO}-${VERSION}/7fa2af80.pub
#sudo apt-key adv --fetch-keys https://developer.download.nvidia.com/compute/cuda/repos/${DISTRO}/${ARCHITECTURE}/7fa2af80.pub
#wget https://developer.download.nvidia.com/compute/cuda/repos/${DISTRO}/${ARCHITECTURE}/cuda-${DISTRO}.pin
#sudo mv cuda-${DISTRO}.pin /etc/apt/preferences.d/cuda-repository-pin-600

wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/cuda-ubuntu2004.pin
sudo mv cuda-ubuntu2004.pin /etc/apt/preferences.d/cuda-repository-pin-600
sudo apt-key adv --fetch-keys https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/7fa2af80.pub
sudo add-apt-repository "deb https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/ /"

sudo apt-get update
sudo DEBIAN_FRONTEND=noninteractive apt-get -y install cuda

MINICONDA_PATH="/miniconda"
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh
bash miniconda.sh -b -p $MINICONDA_PATH && rm miniconda.sh
PATH="${MINICONDA_PATH}/bin:$PATH"
conda init bash
source $HOME/.bashrc
conda update -y -n base -c defaults conda
conda install -y -c conda-forge python=3.8
conda install -y -c conda-forge openmm MDAnalysis MDAnalysisTests ase mpi4py
pip install --ignore-installed grpcio
PYTHON=$MINICONDA_PATH/bin/python
export PATH=$MINICONDA_PATH/bin:$PATH

git clone https://gitlab.com/intangiblerealities/narupa-protocol.git --branch master narupa-protocol
cd narupa-protocol
./compile.sh --no-dotnet
