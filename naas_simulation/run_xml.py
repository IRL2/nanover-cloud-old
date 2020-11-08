#!/usr/bin/env python

"""
Run a simulation of the SRAS-COV2 protease in openMM. Then expose the simulation
with Narupa with IMD.
"""

import os
import sys
import multiprocessing
import time
from xml.dom.minidom import getDOMImplementation, parseString, Element
from io import StringIO
from tempfile import TemporaryDirectory

from simtk import openmm as mm
from simtk.openmm import app
import simtk.unit as unit
from simtk.openmm import app, XmlSerializer

import openmmimd
import pyvmdimd
from narupa.app import NarupaImdApplication, NarupaImdClient
from narupa.vmdimd import Adaptor
from narupa.openmm.converter import openmm_to_frame_data
from narupa.utilities.timing import yield_interval
from narupa.openmm.serializer import _get_node_and_raise_if_more_than_one, serialize_simulation

import networkx

import matplotlib.cm


PLATFORM = 'CUDA'
GRACE_PERIOD_MINUTES = 10
TIMEOUT_MINUTES = 5
VMD_PORT = 9000
VMD_ADDRESS = '127.0.0.1'
NARUPA_PORT = 38801


def deserialize_simulation(
    xml_content: str,
    platform=PLATFORM,
    extra_forces=tuple(),
) -> app.Simulation:
    """
    Create an OpenMM simulation from XML.

    :param xml_content: The content of an XML file as a string.
    :return: An instance of the simulation.
    """
    document = parseString(xml_content)

    pdb_node = _get_node_and_raise_if_more_than_one(document, 'pdb')
    pdb_content = StringIO(pdb_node.firstChild.nodeValue)
    with TemporaryDirectory() as tmp_dir:
        pdb_path = os.path.join(tmp_dir, 'configuration.pdb')
        with open(str(pdb_path), 'w') as outfile:
            outfile.write(pdb_content.getvalue())
        pdb = app.PDBFile(str(pdb_path))

    system_node = _get_node_and_raise_if_more_than_one(document, 'System')
    system_content = system_node.toprettyxml()
    system = XmlSerializer.deserialize(system_content)

    for extra in extra_forces:
        system.addForce(extra)

    integrator_node = _get_node_and_raise_if_more_than_one(document, 'Integrator')
    integrator_content = integrator_node.toprettyxml()
    integrator = XmlSerializer.deserialize(integrator_content)

    platform = mm.Platform.getPlatformByName(platform)

    simulation = app.Simulation(
        topology=pdb.topology,
        system=system,
        integrator=integrator,
        platform=platform,
    )
    simulation.context.setPositions(pdb.positions)
    return simulation


def build_simulation(xml_path, add_imd=True, platform_target=PLATFORM):
    extra_forces = []
    if add_imd:
        wait = False  # whether to wait for a connection before running MD steps
        rate = 20  # rate (in frames) at which to send molecular dynamics positions to the client
        useInternalUnits = False  # whether to output with OpenMM's internal units, or VMD units (angstroms, kCal/mol).
        imdForce = openmmimd.ImdForce(VMD_ADDRESS, VMD_PORT, wait, rate, useInternalUnits)
        extra_forces = [imdForce]
    with open(xml_path) as infile:
        simulation = deserialize_simulation(infile.read(), extra_forces=extra_forces)

    reporter = app.StateDataReporter(sys.stdout, 1000, speed=True)
    simulation.reporters.append(reporter)

    return simulation


def run_inifinite_simulation(xml_path, queue):
    simulation = build_simulation(
        xml_path, add_imd=True, platform_target=PLATFORM)
    print(f'Running on platform {simulation.context.getPlatform().getName()}')
    while queue.empty():
        simulation.step(10000)


def build_topology_frame(simulation):
    topology = simulation.topology
    system = simulation.system
    state = simulation.context.getState(getPositions=True)
    return openmm_to_frame_data(topology=topology, system=system, state=state)


def run_narupa_server(xml_path, queue):
    simulation = build_simulation(xml_path, add_imd=False)
    topology_frame = build_topology_frame(simulation)

    connection = pyvmdimd.IMDClient(VMD_ADDRESS, VMD_PORT)
    connection.set_transmission_rate(5)

    with NarupaImdApplication.basic_server(name='MPro', port=NARUPA_PORT) as server_app:
        print(f'Serving on {server_app.address}:{server_app.port}.')
        queue.put((server_app.address, server_app.port))
        adaptor = Adaptor(
            topology_frame,
            frame_publisher=server_app.frame_publisher,
            imd_service=server_app.imd,
        )
        connection.set_coordinate_observer(adaptor.on_coordinates)
        connection.set_energy_observer(adaptor.on_energies)
        connection.set_force_provider(adaptor.get_forces)

        # At this point, the MD engine must be running as this command
        # run the communication with the VMD server. It may take a long time
        # though so we retry for a while.
        try:
            timeout_end = time.monotonic() + 240
            for _ in yield_interval(1):
                try:
                    connection.loop()
                except OSError as err:
                    if time.monotonic() > timeout_end:
                        raise err
                else:
                    break
        except AssertionError:
            print('Closing Narupa server')


def get_chains(particle_count, bonds):
    graph = networkx.Graph()
    graph.add_nodes_from(range(particle_count))
    graph.add_edges_from(bonds)
    return sorted(networkx.connected_components(graph), key=lambda x: min(x))


def get_matplotlib_gradient(name: str):
    cmap = matplotlib.cm.get_cmap(name)
    return list(list(cmap(x/7)) for x in range(0, 8, 1))


def setup_aestetics(address, port):
    print(f'Client connecting to {address}:{port}.')
    cpk_colours = {
        'N': 'blue',
        'P': '#dca523',
        'C': '#c0c0c0',
        'O': '#fc1c03',
        'S': '#e9ce16',
        'H': '#ffffff',
    }

    with NarupaImdClient.connect_to_single_server(address, port) as client:
        frame = client.wait_until_first_frame()
        chains = get_chains(frame.particle_count, frame.bond_pairs)
        print(f'Found {len(chains)} chains.')

        with client.root_selection.modify():
            client.root_selection.hide = True
        
        prot_chain_0 = client.create_selection('Protein0', chains[0])
        prot_chain_1 = client.create_selection('Protein1', chains[1])
        ligand = client.create_selection('Ligand', chains[2])

        cpk_chain_0 = cpk_colours.copy()
        cpk_chain_0['C'] = '#6a90a6'
        with prot_chain_0.modify():
            prot_chain_0.renderer = {
                'render': 'liquorice',
                'color': {
                    'type': 'cpk',
                    'scheme': cpk_chain_0,
                },
            }
        
        cpk_chain_1 = cpk_colours.copy()
        cpk_chain_1['C'] = '#6b5661'
        with prot_chain_1.modify():
            prot_chain_1.renderer = {
                'render': 'liquorice',
                'color': {
                    'type': 'cpk',
                    'scheme': cpk_chain_1,
                },
            }
        
        with ligand.modify():
            ligand.renderer = {
                'render': 'cpk',
                'color': {
                    'type': 'cpk',
                    'scheme': cpk_colours,
                },
                'particle.scale': 0.15,
                'bond.scale': 0.1,
            }


def is_active_avatar(current_avatars):
    return any(avatar.components for avatar in current_avatars.values())


def run_until_timeout(grace_minutes, timeout_minutes, address, port):
    """
    Loop until the timeout is over.

    The timeout happens after a given number of minutes without VR client
    connected. A grace period at the beginning of the loop give time for the
    first client to connect. A connected VR client is defined as streaming an
    avatar.

    :param grace_minutes: number of minutes at the beginning of the loop during
        which the timeout is ignored
    :param timeout_minutes: number of minutes without VR client connected
        before the function returns
    :param address: The address of the Narupa server for the client to connect
    :param port: The port of the Narupa server for the client to connect
    """
    timeout_seconds = timeout_minutes * 60
    grace_seconds = grace_minutes * 60
    with NarupaImdClient.connect_to_single_server(address, port) as client:
        multiplayer = client._multiplayer_client
        multiplayer.join_avatar_stream()
        now = time.monotonic()
        end_of_grace = now + grace_seconds
        end_of_timeout = now + timeout_seconds
        for _ in yield_interval(1):
            now = time.monotonic()
            if is_active_avatar(multiplayer.current_avatars):
                end_of_timeout = now + timeout_seconds
            if now > end_of_grace and now > end_of_timeout:
                print('Timeout!')
                return


if __name__ == '__main__':
    xml_path = sys.argv[1]

    kill_queue = multiprocessing.Queue()
    server_queue = multiprocessing.Queue()

    openmm_process = multiprocessing.Process(
        target=run_inifinite_simulation, args=(xml_path, kill_queue))
    openmm_process.start()

    try:
        narupa_process = multiprocessing.Process(
            target=run_narupa_server, args=(xml_path, server_queue))
        narupa_process.start()

        localhost = '127.0.0.1'
        address, port = server_queue.get()
        #setup_aestetics(localhost, port)

        run_until_timeout(GRACE_PERIOD_MINUTES, TIMEOUT_MINUTES, localhost, port)
    finally:
        # This stops openMM.
        kill_queue.put('STOP')
