#!/bin/bash
cd /

MINICONDA_PATH="/miniconda"
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh
bash miniconda.sh -b -p $MINICONDA_PATH && rm miniconda.sh
PATH="${MINICONDA_PATH}/bin:$PATH"
conda init bash
source $HOME/.bashrc
conda update -y -n base -c defaults conda
conda install -y -c conda-forge python=3.7
conda install -y -c conda-forge openmm MDAnalysis MDAnalysisTests ase mpi4py
pip install --ignore-installed grpcio
PYTHON=$MINICONDA_PATH/bin/python
export PATH=$MINICONDA_PATH/bin:$PATH

git clone https://gitlab.com/intangiblerealities/narupa-protocol.git --branch master narupa-protocol
cd narupa-protocol
./compile.sh