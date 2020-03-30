#!/bin/bash

sudo iptables -I INPUT 1 -p tcp --dport 38801 -j ACCEPT
sudo iptables -I OUTPUT 1 -p tcp --dport 38801 -j ACCEPT
sudo bash -c "iptables-save > /etc/iptables.rules"

$HOME/miniconda/bin/python $HOME/covid-docker/simulation/poc/run.py