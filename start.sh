#!/bin/bash

INSTANCE_LIFETIME='1h'

function terminate() {
    oci compute instance --auth instance_principal terminate --instance-id $(curl http://169.254.169.254/opc/v1/instance/id)
}

# Limit the lifetime of the instance. Terminate the instance after the given
# duration if nothing else did it before.
(sleep $INSTANCE_LIFETIME; terminate)&

# Open the port.
sudo iptables -I INPUT 1 -p tcp --dport 38801 -j ACCEPT
sudo iptables -I OUTPUT 1 -p tcp --dport 38801 -j ACCEPT
sudo bash -c "iptables-save > /etc/iptables.rules"

# Actually run the narupa server
$HOME/miniconda/bin/python $HOME/covid-docker/simulation/poc/run.py

# Terminate the instance if the script crashed or timed out
terminate