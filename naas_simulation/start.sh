#!/bin/bash

function get_metadata() {
    curl "http://metadata.google.internal/computeMetadata/v1/instance/attributes/$1" -H 'Metadata-Flavor: Google'
}

function terminate() {
    NAME=$(curl http://metadata.google.internal/computeMetadata/v1/instance/name -H 'Metadata-Flavor: Google')
    ZONE=$(curl http://metadata.google.internal/computeMetadata/v1/instance/zone -H 'Metadata-Flavor: Google')
    gcloud --quiet compute instances delete $NAME --zone=$ZONE
}

# Path declarations. TODO: Clean these up
MINICONDA_PATH="/miniconda"
PATH="${MINICONDA_PATH}/bin:$PATH"
source $HOME/.bashrc
PYTHON=$MINICONDA_PATH/bin/python
export PATH=$MINICONDA_PATH/bin:$PATH

# Limit the lifetime of the instance. Terminate the instance at the requested
# end time if it did not terminate before.
# We allow a few minutes of grace period for a better user experience.
end_time=$(get_metadata end_time)
timezone=$(get_metadata timezone)
duration=$($PYTHON ./minutes_until.py ${end_time} ${timezone} 3)
(sleep $duration; terminate)&

# Get the lastest narupa. Master branch is installed on the base image
narupa_protocol_git="https://gitlab.com/intangiblerealities/narupa-protocol.git"
narupa_protocol_git_dir="narupa-protocol"
branch=$(get_metadata branch)
remote_commit=$(git ls-remote $narupa_protocol_git | grep refs/heads/$branch | cut -f 1)
local_commit=$(git -C $narupa_protocol_git_dir rev-parse HEAD)
if [ "$local_commit" != "$remote_commit" ]; then
  rm -rf $narupa_protocol_git_dir
  git clone $narupa_protocol_git --branch $branch $narupa_protocol_git_dir
  cd $narupa_protocol_git_dir
  ./compile.sh
  cd ..
fi

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
