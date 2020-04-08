#!/bin/bash

# Open port 80 to the public.
# Redirect inputs from port 80 to port 8000 that the server listen.
# This allows to expose port 80 without giving the user the proviledges to
# access it directly.

/sbin/iptables -A PREROUTING -t nat -p tcp --dport 80 -j REDIRECT --to-port 8000
/sbin/iptables -I INPUT 1 -p tcp --dport 80 -j ACCEPT
