Work-From-Home Narupa in the cloud
==================================

Offer a quick way to create a cloud instance of Narupa running a
COVID19-relevant simulation. This is to allow researchers working from home
to collaborate about solving the COVID19 crisis by interacting together with
protein-ligand complexes in VR.

*This repository is under active developpement; most features are not yet
implemented.*

How to run
----------

The [`bootstrap.sh`](./bootstrap.sh) script allows to set-up VM image on OCI. The
image is assumed to be based on the "Ubuntu minimal" image provided by Oracle.
An ingress needs to be set to open the port 38801 in TCP for all sources.

Conda needs to be activated to run the simulation script. On a freshly
bootstrapped instance, you may need to source the bashrc.

The proof of concept script sits in [`simulation/poc/run.py`](./simulation/poc/run.py).
If it runs successfully, the output looks as follow:

```
(base) ubuntu@bootstrap:~$ python covid-docker/simulation/poc/run.py
Established socket at 127.0.0.1:9000
Running on platform CUDA
Waiting for IMD connection at 127.0.0.1:9000
Serving on [::]:54321.
Performing handshake
Client connected, awaiting GO command
Client connecting to 127.0.0.1:54321.
Received GO command, starting IMD!
Setting IMD rate5
Found 3 chains.
#"Speed (ns/day)"
0
182
182
182
182
181
181
...
```