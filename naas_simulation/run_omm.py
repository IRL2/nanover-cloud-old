#!/usr/bin/env python

import argparse
import sys
import time
import os
from typing import Dict, Set, Hashable

from xml.dom.minidom import getDOMImplementation, parseString, Element
from io import StringIO
from tempfile import TemporaryDirectory

import numpy as np

from narupa.ase.openmm.runner import OpenMMIMDRunner, ImdParams, LoggingParams
from narupa.openmm.narupareporter import NarupaReporter
from narupa.trajectory.frame_server import (
    PAUSE_COMMAND_KEY, PLAY_COMMAND_KEY, RESET_COMMAND_KEY)
from narupa.app.app_server import NarupaServer
from narupa.essd import DiscoveryServer
from narupa.app import NarupaImdApplication
from narupa.openmm.serializer import _get_node_and_raise_if_more_than_one, serialize_simulation
from narupa.imd.particle_interaction import ParticleInteraction
from narupa.imd.imd_force import calculate_imd_force

from simtk.openmm import app, XmlSerializer, CustomExternalForce, Platform
from simtk import unit

NARUPA_PORT = 38801
DEFAULT_WALLTIME = 30  # minutes
DEFAULT_CONNECTION_DELAY = 5  # minutes
DEFAULT_TIMEOUT = 2  # minutes


class ForceUpdater:
    def __init__(self, report_interval, imd_service, force, energy_reset=None):
        self._reportInterval = report_interval
        self._imd_service = imd_service
        self._force = force

        self.n_particles = force.getNumParticles()
        self.positions = None
        self.masses = None
        self.context = None
        self.is_dirty = False
        self._previous_interactions = {}
        self._not_reset_interactions = {}
        self.energy_reset = energy_reset
        self.need_reset = False
    
    @property
    def has_energy_reset(self):
        return self.energy_reset is not None
    
    # The name of the method is part of the OpenMM API. It cannot be made to
    # conform PEP8.
    # noinspection PyPep8Naming
    def describeNextReport(self, simulation):  # pylint: disable=invalid-name
        steps = self._reportInterval - simulation.currentStep % self._reportInterval
        # The reporter needs:
        # - the positions
        # - not the velocities
        # - not the forces
        # - marybe the energies
        # - positions are unwrapped
        return steps, True, False, False, self.has_energy_reset, True

    def report(self, simulation, state):
        if self.masses is None:
            self.masses = self.get_masses(simulation)
        if self.context is None:
            self.context = simulation.context
        positions = np.asarray(state.getPositions().value_in_unit(unit.nanometer))
        interactions = self._imd_service.active_interactions
        self._update_forces(positions, interactions)
        self._not_reset_interactions.update(interactions)
        self._update_energy_reset(state)
        #self._previous_interactions = dict(interactions)
    
    @staticmethod
    def get_masses(simulation):
        system = simulation.system
        return np.array([
            system.getParticleMass(particle).value_in_unit(unit.dalton)
            for particle in range(system.getNumParticles())
        ])
    

    def _update_energy_reset(self, state):
        if not self.has_energy_reset:
            return
        potential_energy = state.getPotentialEnergy()
        self.need_reset = potential_energy > self.reset_velocities
    
    def _update_forces(self, positions, interactions):
        needs_update = False
        if interactions:
            _, forces_kjmol = calculate_imd_force(
                positions, self.masses, interactions.values(),
            )
            for particle, force in enumerate(forces_kjmol):
                self._force.setParticleParameters(particle, particle, force)
            self.is_dirty = True
            needs_update = True
        elif self.is_dirty:
            for particle in range(self.n_particles):
                self._force.setParticleParameters(particle, particle, (0, 0, 0))
            needs_update = True
            self.is_dirty = False

        if needs_update:
            self._force.updateParametersInContext(self.context)
    
    def reset_velocities(self):
        cancelled_interactions = _get_cancelled_interactions(self._not_reset_interactions, self._previous_interactions)
        atoms_to_reset = _get_atoms_to_reset(cancelled_interactions)
        if len(atoms_to_reset) == 0:
            return
        state = self.context.getState(getVelocities=True)
        velocities = state.getVelocities()
        for atom in atoms_to_reset:
            velocities[atom] = (0, 0, 0)
        self.context.setVelocities(velocities)
        self._previous_interactions = self._not_reset_interactions
        self._not_reset_interactions = {}
        print(atoms_to_reset)
        

class CloudRunner:
    def __init__(self, simulation_path, walltime, connection_delay, timeout, frame_freq=5):
        with open(args.simulation_path) as infile:
            self.simulation, self.imd_force = deserialize_simulation(infile.read())
        self._prepare_force_update()

        self.connection_delay = connection_delay * 60  # in seconds
        self.timeout = timeout * 60  # in seconds
        self.walltime = walltime * 60  # in seconds

        server = NarupaServer(address='[::]', port=NARUPA_PORT)
        discovery = DiscoveryServer()
        self.app_server = NarupaImdApplication(server, discovery, name='Cloud')
        frame_reporter = NarupaReporter(
            report_interval=frame_freq, frame_server=self.app_server.frame_publisher)
        self.simulation.reporters.append(frame_reporter)
        self.force_reporter = ForceUpdater(
            report_interval=10, imd_service=self.app_server.imd, force=self.imd_force)
        self.simulation.reporters.append(self.force_reporter)

        state = self.context.getState(getPositions=True, getVelocities=True)
        self.original_positions = state.getPositions()
        self.original_velocities = state.getVelocities()
        self.original_box = state.getPeriodicBoxVectors()
        self.need_reset = False

        self._running = False
        self._register_commands()
    
    def _prepare_force_update(self):
        self.masses = self.get_masses(self.simulation)
        self.context = self.simulation.context
        self.is_dirty = False
        self.n_particles = self.imd_force.getNumParticles()

    @staticmethod
    def get_masses(simulation):
        system = simulation.system
        return np.array([
            system.getParticleMass(particle).value_in_unit(unit.dalton)
            for particle in range(system.getNumParticles())
        ])
    
    def _reset(self):
        self.context.setPositions(self.original_positions)
        self.context.setVelocities(self.original_velocities)
        self.context.setPeriodicBoxVectors(*self.original_box)
        self.need_reset = False
        self.force_reporter.need_reset = False
    
    def _trigger_reset(self):
        self.need_reset = True
    
    def _update_forces(self):
        state = self.context.getState(getPositions=True)
        positions = np.asarray(state.getPositions().value_in_unit(unit.nanometer))
        needs_update = False
        interactions = self.app_server.imd.active_interactions
        if interactions:
            _, forces_kjmol = calculate_imd_force(
                positions, self.masses, interactions.values(),
            )
            for particle, force in enumerate(forces_kjmol):
                self.imd_force.setParticleParameters(particle, particle, force)
            self.is_dirty = True
            needs_update = True
        elif self.is_dirty:
            for particle in range(self.n_particles):
                self.imd_force.setParticleParameters(particle, particle, (0, 0, 0))
            needs_update = True
            self.is_dirty = False
        if needs_update:
            self.imd_force.updateParametersInContext(self.context)
    
    def _print_forces(self):
        print('=' * 80)
        for particle in range(self.n_particles):
            print(self.imd_force.getParticleParameters(particle))

    def _register_commands(self):
        self.app_server.server.register_command(PAUSE_COMMAND_KEY, self._pause)
        self.app_server.server.register_command(PLAY_COMMAND_KEY, self._play)
        self.app_server.server.register_command(RESET_COMMAND_KEY, self._trigger_reset)
    
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.app_server.close()

    def _pause(self):
        self._running = False
    
    def _play(self):
        self._running = True
    
    def _get_avatars(self):
        return self.app_server._multiplayer._avatars.copy_content()

    def has_active_avatar(self):
        return any(avatar.components for avatar in self._get_avatars().values())
    
    def get_timeout_checker(self):
        starting_time = time.monotonic()
        end_connection_delay = starting_time + self.connection_delay
        end_timeout = starting_time + self.timeout
        end_walltime = starting_time + self.walltime
        while True:
            now = time.monotonic()
            if self.has_active_avatar():
                end_timeout = now + self.timeout
            passed_walltime = now > end_walltime
            passed_timeout = now > end_connection_delay and now > end_timeout
            yield passed_walltime or passed_timeout
    
    def run(self, iteration_size=10):
        iteration_size = 10
        n_iterations = 0
        self._running = True
        timeout_cheker = self.get_timeout_checker()
        print('ready to go')
        while True:
            if self._running:
                #self._update_forces()
                try:
                    self.simulation.step(iteration_size)
                except:
                    self.need_reset = True
                self.force_reporter.reset_velocities()
                if self.need_reset or self.force_reporter.need_reset:
                    self._reset()
                n_iterations += 1
            else:
                time.sleep(0.3)
        self._running = False


def deserialize_simulation(
    xml_content: str,
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

    force = CustomExternalForce('-fx * x - fy * y - fz * z')
    force.addPerParticleParameter('fx')
    force.addPerParticleParameter('fy')
    force.addPerParticleParameter('fz')
    for particle in range(system.getNumParticles()):
        force.addParticle(particle, (0, 0, 0))
    system.addForce(force)

    integrator_node = _get_node_and_raise_if_more_than_one(document, 'Integrator')
    integrator_content = integrator_node.toprettyxml()
    integrator = XmlSerializer.deserialize(integrator_content)

    simulation = app.Simulation(
        topology=pdb.topology,
        system=system,
        integrator=integrator,
        #platform=Platform.getPlatformByName('CUDA')
    )
    simulation.context.setPositions(pdb.positions)
    return simulation, force


def _get_cancelled_interactions(interactions, previous_interactions) -> Dict[object, ParticleInteraction]:
    old_keys = set(previous_interactions.keys())
    cancelled_interactions = old_keys.difference(interactions.keys())
    return {key: previous_interactions[key] for key in cancelled_interactions}


def _get_atoms_to_reset(cancelled_interactions) -> Set[int]:
    atoms_to_reset = set()
    for key, interaction in cancelled_interactions.items():
        if interaction.reset_velocities or True:
            atoms_to_reset = atoms_to_reset.union(interaction.particles)
    return atoms_to_reset


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('simulation_path')
    arg_parser.add_argument(
        '--walltime', type=float, default=DEFAULT_WALLTIME,
        help='Maximum duration of a session, in minutes.',
    )
    arg_parser.add_argument(
        '--connection-delay', type=float, default=DEFAULT_CONNECTION_DELAY,
        help='Duration alowed for the first avatar to connect, in minutes.'
    )
    arg_parser.add_argument(
        '--timeout', type=float, default=DEFAULT_TIMEOUT,
        help='Duration between the last avatar is seen and the session end, '
             'in minutes.',
    )
    arg_parser.add_argument(
        '--frame-frequency', type=int, default=5,
    )
    arg_parser.add_argument(
        '--iteration-size', type=int, default=10,
    )
    args = arg_parser.parse_args()

    runner = CloudRunner(
        args.simulation_path,
        walltime=args.walltime,
        connection_delay=args.connection_delay,
        timeout=args.timeout,
        frame_freq=args.frame_frequency,
    )
    with runner:
        runner.run(iteration_size=args.iteration_size)
