import os
from collections import namedtuple
from . import utils
import requests
import googleapiclient.discovery

PROJECT = 'narupa-web-ui'
NAAS_SIMULATION_TARBALL = os.environ.get('NAAS_SIMULATION_TARBALL')


def get_compute_client():
    return googleapiclient.discovery.build('compute', 'v1', cache_discovery=False)


# Based on GPU availability from https://cloud.google.com/compute/docs/gpus#gpus-list
def get_zone_for_region(region):
    region_to_zone = {
        'asia-east1': 'a',              # Taiwan
        'asia-northeast1': 'a',         # Tokyo
        'asia-northeast3': 'b',         # Seoul
        'asia-south1': 'a',             # Mumbai
        'asia-southeast1': 'b',         # Singapore
        'europe-west2': 'a',            # London
        'europe-west3': 'b',            # Frankfurt
        'europe-west4': 'b',            # Netherlands
        'southamerica-east1': 'c',      # Sao Paolo
        'us-central1': 'a',             # Iowa
        'us-east1': 'c',                # South Carolina
        'us-east4': 'b',                # North Virginia
        'us-west1': 'a'                 # Oregon
    }
    zone = region_to_zone.get(region, None)
    return '{}-{}'.format(region, zone)


def choose_image(tag: str) -> str:
    """
    Look for the latest VM image with the requested tag set to 'true'.

    This VM image is the one to use for that tag. The function returns the name
    of the image if one is found, and raises a ValueError otherwise.
    """
    Image = namedtuple('Image', ['timestamp', 'name'])
    result = []
    service = get_compute_client()
    request = service.images().list(project=PROJECT)
    while request is not None:
        response = request.execute()
        for image in response['items']:
            if image.get('labels', {}).get(tag) == 'true':
                result.append(Image(image['creationTimestamp'], image['name']))
        request = service.images().list_next(
            previous_request=request, previous_response=response)
    if not result:
        raise ValueError(f'No image was found with the tag "{tag}" set to true.')
    # Ideally, the filtering and the sorting should be done directly in the
    # API with the orderBy and the filter arguments. I did not manage yet,
    # though.
    return sorted(result)[-1].name


# https://cloud.google.com/compute/docs/reference/rest/v1/instances/insert
def create_instance(tag, region, branch, runner, duration, end_time, timezone, simulation=None, topology=None, trajectory=None):
    zone = get_zone_for_region(region)

    machine_type = 'n1-highcpu-2'
    gpu_type = 'nvidia-tesla-t4'
    disk_size_gb = '50'

    name = 'narupa-simulation-{}'.format(utils.generate_short_id())
    metadata = [
        { 'key': 'google-logging-enabled', 'value': 'true' },
        { 'key': 'branch', 'value': branch },
        { 'key': 'runner', 'value': runner },
        { 'key': 'duration', 'value': duration },
        { 'key': 'end_time', 'value': end_time },
        { 'key': 'timezone', 'value': timezone },
        { 'key': 'startup-script', 'value': '#!/bin/bash\nwget -O tmp.tar "{}"\ntar xf tmp.tar --strip-components=2\nchmod +x start.sh\n./start.sh'.format(NAAS_SIMULATION_TARBALL)}
    ]
    if simulation:
        metadata.append({ 'key': 'simulation', 'value': simulation })
    if topology:
        metadata.append({ 'key': 'topology', 'value': topology })
    if trajectory:
        metadata.append({ 'key': 'trajectory', 'value': trajectory })

    config = {
        'name': name,
        'zone': 'projects/{}/zones/{}'.format(PROJECT, zone),
        'machineType': 'projects/{}/zones/{}/machineTypes/{}'.format(PROJECT, zone, machine_type),
        'displayDevice': {
            'enableDisplay': False
        },
        'metadata': {
            'items': metadata
        },
        'tags': {
            'items': [ 'narupa-simulation' ]
        },
        'guestAccelerators': [
            {
            'acceleratorCount': 1,
            'acceleratorType': 'projects/{}/zones/{}/acceleratorTypes/{}'.format(PROJECT, zone, gpu_type)
            }
        ],
        'disks': [
            {
            'type': 'PERSISTENT',
            'boot': True,
            'mode': 'READ_WRITE',
            'autoDelete': True,
            'deviceName': name,
            'initializeParams': {
                "sourceImage": "projects/narupa-web-ui/global/images/{}".format(choose_image(tag)),
                'diskType': 'projects/{}/zones/{}/diskTypes/pd-standard'.format(PROJECT, zone),
                'diskSizeGb': disk_size_gb
            },
            'diskEncryptionKey': {}
            }
        ],
        'canIpForward': False,
        'networkInterfaces': [
            {
            'subnetwork': 'projects/{}/regions/{}/subnetworks/default'.format(PROJECT, region),
            'accessConfigs': [
                {
                'name': 'External NAT',
                'type': 'ONE_TO_ONE_NAT',
                'networkTier': 'PREMIUM'
                }
            ]
            }
        ],
        'serviceAccounts': [
            {
            'email': '467879059099-compute@developer.gserviceaccount.com',
            'scopes': [
                'https://www.googleapis.com/auth/cloud-platform',
                'https://www.googleapis.com/auth/devstorage.read_only',
                'https://www.googleapis.com/auth/logging.write',
                'https://www.googleapis.com/auth/monitoring.write',
                'https://www.googleapis.com/auth/servicecontrol',
                'https://www.googleapis.com/auth/service.management.readonly',
                'https://www.googleapis.com/auth/trace.append'
            ]
            }
        ],
        'scheduling': {
            'preemptible': False,
            'onHostMaintenance': 'TERMINATE',
            'automaticRestart': False
        },
        'deletionProtection': False,
        'shieldedInstanceConfig': {
            'enableSecureBoot': False,
            'enableVtpm': True,
            'enableIntegrityMonitoring': True
        }
    }

    response = get_compute_client().instances().insert(project=PROJECT, zone=zone, body=config).execute()
    response['instanceName'] = name
    return response


# https://cloud.google.com/compute/docs/reference/rest/v1/instances/get
def get_instance(region, name):
    zone = get_zone_for_region(region)
    try:
        response = get_compute_client().instances().get(project=PROJECT, zone=zone, instance=name).execute()
        ip = response['networkInterfaces'][0]['accessConfigs'][0]['natIP']
        response['instanceIp'] = ip
        response['narupaStatus'] = get_narupa_status(ip)
        return response
    except Exception:
        return {'narupaStatus': False, 'status': 'UNKNOWN'}



# https://cloud.google.com/compute/docs/reference/rest/v1/instances/delete
def delete_instance(region, name):
    zone = get_zone_for_region(region)
    get_compute_client().instances().delete(project=PROJECT, zone=zone, instance=name).execute()


def get_narupa_status(ip):
    try:
        response = requests.get('http://{}:5000/api/status'.format(ip), timeout=5)
        return response.json()['status']
    except Exception:
        return False
