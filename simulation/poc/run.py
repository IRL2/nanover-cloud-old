#!/usr/bin/env python

"""
Run a simulation of the SRAS-COV2 protease in openMM. Then expose the simulation
with Narupa with IMD.
"""

import sys
import multiprocessing
import time

from simtk import openmm as mm
from simtk.openmm import app
import simtk.unit as unit

import openmmimd
import pyvmdimd
from narupa.app import NarupaImdApplication, NarupaImdClient
from narupa.vmdimd import Adaptor
from narupa.openmm.converter import openmm_to_frame_data

import networkx

import matplotlib.cm


VMD_PORT = 9000
VMD_ADDRESS = '127.0.0.1'

# These files were provided by Helen with the following caveat:
# > here are the inputs I have been using for a "proof of principle"
# > simulation of MPro and a known inhibitor. Positions are in pdb format,
# > not inpcrd. Simulation has been tested and does work for undocking and
# > redocking purposes, but one thing to keep a mental note of it that the
# > C terminus of the protein subunits are missing a few residues. I plan to
# > fix this in a later iteration of the simulation, but for time purposes,
# > I have been simulating as-is.
PRMTOP = '6y2g_neutral_mono.prmtop'
PDB = 'output.pdb'


def build_simulation(prmtop_path, pdb_path, add_imd=True):
    prmtop = app.AmberPrmtopFile(prmtop_path)
    system = prmtop.createSystem(
        nonbondedMethod=app.CutoffNonPeriodic,
        nonbondedCutoff=1 * unit.nanometer,
        constraints=app.HBonds,
    )
    if add_imd:
        wait = True  # whether to wait for a connection before running MD steps
        rate = 20  # rate (in frames) at which to send molecular dynamics positions to the client
        useInternalUnits = False  # whether to output with OpenMM's internal units, or VMD units (angstroms, kCal/mol).
        imdForce = openmmimd.ImdForce(VMD_ADDRESS, VMD_PORT, wait, rate, useInternalUnits)
        system.addForce(imdForce)
    integrator = mm.LangevinIntegrator(
        300 * unit.kelvin,
        1 / unit.picosecond,
        0.002 * unit.picoseconds,
    )
    simulation = app.Simulation(prmtop.topology, system, integrator)

    box_length = 10 * unit.nanometer
    pdb = app.PDBFile(pdb_path)
    simulation.context.setPositions(pdb.positions)
    simulation.context.setPeriodicBoxVectors(
        [box_length, 0, 0],
        [0, box_length, 0],
        [0, 0, box_length],
    )

    return simulation


def run_inifinite_simulation(prmtop_path, pdb_path, queue):
    simulation = build_simulation(prmtop_path, pdb_path)
    while queue.empty():
        simulation.step(10000)


def build_topology_frame(simulation):
    topology = simulation.topology
    system = simulation.system
    return openmm_to_frame_data(topology=topology, system=system)


def run_narupa_server(prmtop_path, pdb_path, queue):
    simulation = build_simulation(PRMTOP, PDB, add_imd=False)
    topology_frame = build_topology_frame(simulation)

    connection = pyvmdimd.IMDClient(VMD_ADDRESS, VMD_PORT)
    connection.set_transmission_rate(10)

    with NarupaImdApplication.basic_server(name='VMD-test') as server_app:
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
        # run the communication with the VMD server.
        connection.loop()


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


if __name__ == '__main__':
    kill_queue = multiprocessing.Queue()
    server_queue = multiprocessing.Queue()

    openmm_process = multiprocessing.Process(
        target=run_inifinite_simulation, args=(PRMTOP, PDB, kill_queue))
    openmm_process.start()

    narupa_process = multiprocessing.Process(
        target=run_narupa_server, args=(PRMTOP, PDB, server_queue))
    narupa_process.start()

    address, port = server_queue.get()
    setup_aestetics('127.0.0.1', port)

    # Since everything is running in the background, we need something to keep
    # the main process busy.
    while True:
        time.sleep(1)

    # This stops openMM
    kill_queue.put('STOP')