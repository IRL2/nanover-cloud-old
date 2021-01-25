#!/bin/bash

function get_metadata() {
    curl "http://metadata.google.internal/computeMetadata/v1/instance/attributes/$1" -H 'Metadata-Flavor: Google'
}

function terminate() {
    NAME=$(curl http://metadata.google.internal/computeMetadata/v1/instance/name -H 'Metadata-Flavor: Google')
    ZONE=$(curl http://metadata.google.internal/computeMetadata/v1/instance/zone -H 'Metadata-Flavor: Google')
    gcloud --quiet compute instances delete $NAME --zone=$ZONE
}

# Limit the lifetime of the instance. Terminate the instance after the given
# duration if nothing else did it before.
duration=$(get_metadata duration)
(sleep $duration; terminate)&

# Install conda
MINICONDA_PATH="$HOME/miniconda"
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

# Get the lastest narupa
branch=$(get_metadata branch)
if [[ $(echo $branch | grep html | wc -l) -gt 0 ]]; then
    branch='master'
fi
rm -rf narupa-protocol
git clone https://gitlab.com/intangiblerealities/narupa-protocol.git --branch $branch narupa-protocol
cd narupa-protocol
./compile.sh
cd ..

# Start the http helper server
(FLASK_APP=simulation_server.py $PYTHON -m flask run --host=0.0.0.0)&

# Actually run the narupa server
runner_request=$(get_metadata runner)
case "${runner_request}" in
    'ase')
        echo "Runner is ase"
        echo "Getting simulation"
        filename=$(get_metadata simulation)
        wget -O simulation.xml "${filename}"
        narupa-omm-ase simulation.xml
        ;;
    'omm')
        echo "Runner is omm"
        echo "Getting simulation"
        filename=$(get_metadata simulation)
        wget -O simulation.xml "${filename}"
        narupa-omm-server simulation.xml
        ;;
    'trajectory')
        echo "Runner is trajectory"
        echo "Getting topology"
        filename=$(get_metadata topology)
        topology="$(basename $filename)"
        wget -O $topology "${filename}"
        echo "Getting trajectory"
        filename=$(get_metadata trajectory)
        trajectory="$$(basename $filename)"
        wget -O $trajectory "${filename}"
        $PYTHON run_traj.py $topology $trajectory
        ;;
esac

# Terminate the instance if the script crashed or timed out
terminate
