Work-From-Home Narupa in the cloud
==================================

This project allows to create a cloud-hosted instance of
[Narupa](https://gitlab.com/intangiblerealities/narupa-protocol) to share a
multi-user virtual reality workspace around a dynamic and interactive
molecular system. A user can use a web page or a web API to create a compute
instance. When the computeinstance is ready, the user receives the IP address of
the instance that can be used in
[Narupa iMD](https://gitlab.com/intangiblerealities/narupa-applications/narupa-imd)
and shared with other users.

The project is exposed at <https://staging.narupa.xyz/git>.

## User guide

The process works in 3 steps: creating an instance, connecting to the instance,
and terminating the instance.

### Creating a compute instance

In order to create an instance, open <https://staging.narupa.xyz/git> in a
browser. The web page contains a form to describe the instance to create.
The fields are:

* "Branch": the git branch to use for the server. The compute instance will
  clone the required branch from
  [narupa-protocol](https://gitlab.com/intangiblerealities/narupa-protocol).
  This allows to use experimental versions of the server. In most case, set the
  field to "master" to use the current version.
* "Simulation": the input file to use for the simulation. Input files are
  downloaded from
  [a repository of input files](https://gitlab.com/intangiblerealities/narupacloud/narupa-cloud-simulation-inputs).
  See the documentation on [how to add new simulations](#adding-a-simulation).
* "Runner": choose between the ASE or the OpenMM runner. The ASE runner uses
  ASE as the integrator and OpenMM to calculate the forces of the system. It is
  the most feature complete runner regarding Narupa feature, but misses some
  features of OpenMM such as holomonic constraints. The OpenMM runner is
  experimental and misses some features of Narupa. It uses OpenMM for both the
  force calculation and the integration.
* "Region": several data centers can host a compute instance. Choose the data
  center the closest to your location to reduce the latency. Note however, that
  we have more ressources available in Frankfurt than in the other centers.

When the fields are completed, click on the "Launch" button to start the
instance. The order is placed and you will be redirected to the status page for
your instance.

### Connecting to the instance

Creating the instance can take several minutes. The status page indicates what
is happening. When the compute instance is ready, the status page displays its
IP address.

When the IP address is available, copy it and open
[Narupa iMD](https://gitlab.com/intangiblerealities/narupa-applications/narupa-imd).
On the screen UI (not in the virtual reality headset), click on the "Direct
connect" button and paste the IP in the "Address" field that appears. Keep the
fields about ports to their default value of 38801 and click "Connect". The
simulation appears in your virtual reality headset.

To allow other users to connect to the same simulation, share the link to the
status page or the IP address of the compute instance. When the other users
have the IP address, they can connect to the simulation by following the same
procedure in Narupa iMD.

Anybody with the IP address can connect to the simulation.

### Terminating the instance

A compute instance remains active for 30 minutes, after which it terminates
itself. When in a simulation, this translates into the dynamics and the other
players avatar freezing. The status page indicates that the instance is
unavailable.

If you are done with the instance before the end of the 30 minutes, you can
terminate it by clicking the "Cancel the instance" link on the status page.
This saves ressources on our side, thank you.

## API reference

Besides the web page, the service is accessible programatically via a REST API.

### Creating an instance

Send a `POST` request to `/api/v1/instance`. The request *must* have the header
`Content-type: application/json`. The arguments are provided as json in the body
of the request. The keys are:

* `simulation` (required): The name of the simulation input file. Valid values
  are names appearing in the input repository
  [manifest](https://gitlab.com/intangiblerealities/narupacloud/narupa-cloud-simulation-inputs/-/blob/master/manifest.txt).
* `branch` (optional): The branch a narupa-protocol to use. Any branch in
  <https://gitlab.com/intangiblerealities/narupa-protocol> is a valid value for
  the field. The default is "master".
* `runner` (optional): The program to use to run the simulation. The valid
  values are "ase" for the ASE runner and "omm" for the OpenMM one. The default
  value is "ase".
* `region` (optional): The region where to start the compute instance. Valid
  values are "Frankfurt", "London", and "Ashburn". The default value is
  "Frankfurt".

If the request is misformated, or if the `simulation` field is missing, the
server responds with a 400 error (Bad request). If the region is invalid, the
server responds with a 404 error (Not found). Otherwise, the server responds
with a 200 code and a json payload.

The response json payload contains 1 or 2 values. If the creation succeeded,
the json contains a `status` key vith the value "success", and a key `jobid`
with the identyfier of the instance as a value. That identifier allows to
refer to the instance in the other entry points of the API. The creation of the
instance can fail in two ways: if there are not enough ressources available
to launch an instance, then the json payload has the form `{"status": "not
enough ressources"}`, if any other error occurs, then the json payload has
the form `{"status": "failed"}`.

## Adding a simulation

## Advanced API entry points

## Dev guide
