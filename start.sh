#!/bin/bash

INSTANCE_LIFETIME='30m'
NARUPA_BRANCH='master'
API_URL='http://169.254.169.254/opc/v1/instance'

function get_metadata() {
    curl "${API_URL}/metadata/$1"
}

function terminate() {
    echo y | $HOME/bin/oci compute instance --auth instance_principal terminate --instance-id $(curl http://169.254.169.254/opc/v1/instance/id)
}

# Limit the lifetime of the instance. Terminate the instance after the given
# duration if nothing else did it before.
(sleep $INSTANCE_LIFETIME; terminate)&

# Open the port.
sudo iptables -I INPUT 1 -p tcp --dport 38801 -j ACCEPT
sudo iptables -I OUTPUT 1 -p tcp --dport 38801 -j ACCEPT
sudo bash -c "iptables-save > /etc/iptables.rules"


# Get the lastest narupa
export PATH=$HOME/miniconda/bin:$PATH
branch=$(get_metadata branch)
if [[ $(echo $branch | grep html | wc -l) -gt 0 ]]; then
    branch=${NARUPA_BRANCH}
fi
rm -rf $HOME/narupa-protocol
git clone https://gitlab.com/intangiblerealities/narupa-protocol.git --branch $branch $HOME/narupa-protocol
cd $HOME/narupa-protocol
./compile.sh
cd $HOME

# Actually run the narupa server
PYTHON=$HOME/miniconda/bin/python
runner_request=$(get_metadata runner)
case "${runner_request}" in
    'ase')
        echo "Runner is ase"
        echo "Getting simulation"
        filename=$(get_metadata simulation)
        wget -O $HOME/simulation.xml "${filename}"
        $PYTHON $HOME/covid-docker/run_ase.py $HOME/simulation.xml
        ;;
    'omm')
        echo "Runner is omm"
        echo "Getting simulation"
        filename=$(get_metadata simulation)
        wget -O $HOME/simulation.xml "${filename}"
        $PYTHON $HOME/covid-docker/run_omm.py $HOME/simulation.xml
        ;;
    'trajectory')
        echo "Runner is trajectory"
        echo "Getting topology"
        filename=$(get_metadata topology)
        topology="$HOME/$(basename $filename)"
        wget -O $topology "${filename}"
        echo "Getting trajectory"
        filename=$(get_metadata trajectory)
        trajectory="$HOME/$(basename $filename)"
        wget -O $trajectory "${filename}"
        $PYTHON $HOME/covid-docker/run_traj.py $topology $trajectory
        ;;
esac

# Terminate the instance if the script crashed or timed out
terminate
