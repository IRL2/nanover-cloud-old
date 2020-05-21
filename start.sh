#!/bin/bash

INSTANCE_LIFETIME='30m'
NARUPA_BRANCH='master'

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

# Download the input file
filename=$(curl http://169.254.169.254/opc/v1/instance/metadata/filename)
#filename='40-ALA.narupa2.xml'
echo "Trying to get ${filename}"
$HOME/bin/oci --auth instance_principal os object get --namespace uobvr --bucket-name naas-bucket --name $filename --file $HOME/simulation.xml

# Get the lastest narupa
export PATH=$HOME/miniconda/bin:$PATH
branch=$(curl http://169.254.169.254/opc/v1/instance/metadata/branch)
if [[ $(echo $branch | grep html | wc -l) -gt 0 ]]; then
    branch=${NARUPA_BRANCH}
fi
rm -rf $HOME/narupa-protocol
git clone https://gitlab.com/intangiblerealities/narupa-protocol.git --branch $branch $HOME/narupa-protocol
cd $HOME/narupa-protocol
./compile.sh
cd $HOME

# Actually run the narupa server
$HOME/miniconda/bin/python $HOME/covid-docker/run_ase.py $HOME/simulation.xml

# Terminate the instance if the script crashed or timed out
terminate
