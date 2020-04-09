#!/bin/bash

# Prepare an Ubuntu image to run the web server.

set -eo pipefail

MINICONDA_PATH="$HOME/miniconda"

sudo apt-get update
sudo apt-get upgrade -y  # We are responsible for keeping the OS up to date
sudo apt-get install -y git authbind

# We package Narupa using conda. Here we install conda.
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh
bash miniconda.sh -b -p $MINICONDA_PATH && rm miniconda.sh
PATH="${MINICONDA_PATH}/bin:$PATH"
conda init bash
source $HOME/.bashrc
conda update -y -n base -c defaults conda

# Get the code
git clone https://gitlab.com/intangiblerealities/covid-docker.git
cd covid-docker

# We need narupa-core to poke servers
conda install -y -c irl -c conda-forge narupa-core

# We need some packages to run the server
pip install -r naas_server/requirements.txt

# We use authbind to let the server run on port 80 without running as root.
# Authbind allows a user access to a port if that user can execute the
# corresponding config file.
sudo touch /etc/authbind/byport/80
sudo chown ubuntu /etc/authbind/byport/80
chmod 500 /etc/authbind/byport/80

# We add the service to be started at boot time
sudo cp naas_server/naas_server.service /etc/systemd/system
sudo systemctl enable naas_server.service
