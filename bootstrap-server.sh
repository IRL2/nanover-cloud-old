#!/bin/bash

# Prepare an Ubuntu image to run the web server.

set -eo pipefail

MINICONDA_PATH="$HOME/miniconda"

function show_help() {
    cat << EOF
Usage ${0##*/} [-b BRANCH] [SERVER_NAME]
Bootstrap a head node for narupa as a service. Tell nginx that the server
is called SERVER_NAME. If the name is not provided, the public IP is used
instead. Naming the server is required if one want to use https.

    -b BRANCH  use a specific branch when cloning the covid-docker repository
EOF
}


OPTIND=1 

branch='master'
server_name=$(wget -qO - icanhazip.com)

while getopts "hb:" opt; do
    case "$opt" in
        h)
            show_help
            exit 0
            ;;
        b)
            branch=$OPTARG
            ;;
    esac
done
shift $((OPTIND-1))
[ "${1:-}" = "--" ] && shift

if [[ $# -gt 0 ]]; then
    server_name=$1
    shift
fi

sudo apt-get update
sudo apt-get upgrade -y  # We are responsible for keeping the OS up to date
sudo apt-get install -y git authbind nginx

# We package Narupa using conda. Here we install conda.
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh
bash miniconda.sh -b -p $MINICONDA_PATH && rm miniconda.sh
PATH="${MINICONDA_PATH}/bin:$PATH"
conda init bash
source $HOME/.bashrc
conda update -y -n base -c defaults conda

# Get the code
git clone https://gitlab.com/intangiblerealities/covid-docker.git --branch $branch
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

# Setup nginx
sudo sed -e "s/DOMAIN_NAME/${server_name}/g" naas_server/nginx.config | sudo tee /etc/nginx/sites-available/naas_server
sudo ln -s /etc/nginx/sites-available/naas_server /etc/nginx/sites-enabled
sudo systemctl enable nginx