FROM ubuntu:latest
#FROM nvidia/cuda
RUN apt-get update && apt-get install -y bzip2 build-essential wget git curl unzip cmake

RUN apt-get install -y software-properties-common
RUN wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu1804/x86_64/cuda-ubuntu1804.pin
RUN mv cuda-ubuntu1804.pin /etc/apt/preferences.d/cuda-repository-pin-600
RUN apt-key adv --fetch-keys https://developer.download.nvidia.com/compute/cuda/repos/ubuntu1804/x86_64/7fa2af80.pub
RUN add-apt-repository "deb http://developer.download.nvidia.com/compute/cuda/repos/ubuntu1804/x86_64/ /"
RUN apt-get update
RUN apt-get -y install cuda

RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh
RUN bash miniconda.sh -b -p /miniconda && rm miniconda.sh
ENV PATH="/miniconda/bin:$PATH"
RUN conda init bash
RUN conda update -n base -c defaults conda

RUN wget https://gitlab.com/intangiblerealities/narupa-protocol/-/jobs/482974372/artifacts/download -O artifacts.zip
RUN unzip artifacts.zip
RUN conda install -c omnia -c conda-forge -c ./conda-bld narupa-openmm narupa-pyvmdimd swig networkx matplotlib
#RUN conda install -c omnia -c conda-forge cudatoolkit-dev
RUN pip install --ignore-installed grpcio

RUN git clone https://gitlab.com/intangiblerealities/narupaplugins/openmm-vmd-imd.git
RUN mkdir build
RUN cd build && cmake /openmm-vmd-imd -DOPENMM_DIR=/miniconda -DCMAKE_INSTALL_PREFIX=/miniconda -DUSE_OLD_CXX11_ABI=on -DCMAKE_BUILD_TYPE=RELEASE
RUN cd build && make && make install && make PythonInstall

RUN apt-get -y remove wget

COPY simulation /simulation
CMD ["python", "/simulation/poc/run.py"]
