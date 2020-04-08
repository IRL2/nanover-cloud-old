#!/bin/bash

/sbin/iptables -I INPUT 1 -p tcp --dport 80 -j ACCEPT
