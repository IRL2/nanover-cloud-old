FROM ubuntu:latest
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y bzip2 build-essential wget git curl unzip cmake

# Install cuda from the nvidia repository
# TODO: installing the "cuda" package comes with hundreds of packages as
#       dependencies. Find the minimum package list to install.
RUN apt-get install -y software-properties-common
RUN wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu1804/x86_64/cuda-ubuntu1804.pin
RUN mv cuda-ubuntu1804.pin /etc/apt/preferences.d/cuda-repository-pin-600
RUN apt-key adv --fetch-keys https://developer.download.nvidia.com/compute/cuda/repos/ubuntu1804/x86_64/7fa2af80.pub
RUN add-apt-repository "deb http://developer.download.nvidia.com/compute/cuda/repos/ubuntu1804/x86_64/ /"
RUN apt-get update
RUN apt-get -y install cuda-10-1

# We package Narupa using conda. Here we install conda.
RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh
RUN bash miniconda.sh -b -p /miniconda && rm miniconda.sh
ENV PATH="/miniconda/bin:$PATH"
RUN conda init bash
RUN conda update -n base -c defaults conda

# The simulation script we aim to run uses features that are not yet merged
# into master, and therefore not available on anaconda cloud. We get the conda
# packages from the CI on the feature/python-vmd-imd branch.
RUN wget https://gitlab.com/intangiblerealities/narupa-protocol/-/jobs/486607716/artifacts/download -O artifacts.zip
RUN unzip artifacts.zip
RUN conda install -c omnia/label/cuda101 -c conda-forge -c ./conda-bld narupa-openmm narupa-pyvmdimd swig networkx matplotlib
# The grpcio package from conda-forge seems to have an issue with SO_REUSE_PORT.
# We overwrite the package by the one provided on pypi that does not have the
# problem.
# TODO: report the issue upstream.
RUN pip install --ignore-installed grpcio

# Compile the vmd-imd plugin for openMM
RUN git clone https://gitlab.com/intangiblerealities/narupaplugins/openmm-vmd-imd.git
RUN mkdir build
RUN cd build && cmake /openmm-vmd-imd -DOPENMM_DIR=/miniconda -DCMAKE_INSTALL_PREFIX=/miniconda -DUSE_OLD_CXX11_ABI=on -DCMAKE_BUILD_TYPE=RELEASE
RUN cd build && make && make install && make PythonInstall

COPY simulation /simulation
CMD ["python", "/simulation/poc/run.py"]