import requests
import datetime
import uuid
import json
import logging
import oci
from . import libinstance
from flask import render_template, url_for, redirect, request, jsonify
from werkzeug.exceptions import BadRequest, NotFound
from app import app

START_TIME = datetime.datetime.now()
logging.basicConfig(
    filename=f'{START_TIME:%Y%m%d-%H%M%S}.log',
    level=logging.INFO,
)


STATES_AVAILABLE = (
    oci.core.models.Instance.LIFECYCLE_STATE_PROVISIONING,
    oci.core.models.Instance.LIFECYCLE_STATE_RUNNING,
)
DEFAULT_FILENAME = 'helen.xml'
MANIFEST = 'https://gitlab.com/intangiblerealities/narupacloud/narupa-cloud-simulation-inputs/-/raw/master/manifest.txt'
REGIONS = {
    'Frankfurt': {'url': 'https://staging.narupa.xyz', 'string': 'eu-frankfurt-1'},
    'London': {'url': 'http://152.67.129.75', 'string': 'uk-london-1'},
    'Ashburn': {'url': 'http://129.213.120.237', 'string': 'iad'},
}
REGION_STRINGS = {
    description['string']: region
    for region, description in REGIONS.items()
}
BASE_REGION = 'Frankfurt'
NOT_ENOUGH_RESSOURCES = 'not enough ressources'


def available_inputs():
    response = requests.get(MANIFEST).content.decode('utf-8-sig')
    return response.splitlines()

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html', launch_url=url_for('launch'))


@app.route('/isness')
def isness():
    return render_template('index.html', launch_url=url_for('launch', filename='40-ALA.narupa2.xml'))


@app.route('/git')
def git():
    simulation_list = available_inputs()
    return render_template(
        'gitindex.html',
        launch_url=url_for('gitlaunch'),
        simulation_list=simulation_list,
        region_list=libinstance.INSTANCE_PARAM.keys(),
    )


@app.route('/launch', defaults={'filename': None, 'image': 'default'})
@app.route('/launch/<filename>', defaults={'image': 'default'})
@app.route('/launch/<filename>/<image>')
def launch(filename=None, image='default'):
    return launch_instance(filename=filename, image=image)


@app.route('/gitlaunch', methods=['POST'])
def gitlaunch():
    data = json.dumps(request.form)
    response = requests.post(
        REGIONS[BASE_REGION]['url']
        + url_for('api_launch'),
        data=data,
        headers={"Content-Type": "application/json"},
    )
    response.raise_for_status()
    response_json = response.json()
    if response_json['status'] == 'success':
        job_id = response_json['jobid']
        return redirect(url_for('status', job_id=job_id))
    elif response_json['status'] == NOT_ENOUGH_RESSOURCES:
        logging.warning(f'Not enough ressources for request {data}.')
        return 'No resource available. Try again later.'


def launch_instance(filename=None, region='Frankfurt', image='default', extra_meta={}):
    if filename is None:
        filename = DEFAULT_FILENAME
    try:
        job_id = libinstance.launch_compute_instance(
                filename, region=region, image=image, extra_meta=extra_meta)
    except libinstance.NotEnoughRessources:
        return 'No resource available. Try again later.'
    #except Exception as err:
    #    print(err)
    #    return 'Something unexpected happened.'
    return redirect(url_for('status', job_id=job_id))


@app.route('/status/<job_id>')
def status(job_id):
    variables = requests.get(
        REGIONS[BASE_REGION]['url']
        + url_for('api_status', job_id=job_id)
    ).json()
    variables['terminate_url'] = url_for('terminate', job_id=job_id)
    return render_template('status.html', **variables)


@app.route('/terminate/<job_id>')
def terminate(job_id):
    requests.delete(
        REGIONS[BASE_REGION]['url']
        + url_for('api_status', job_id=job_id)
    )
    return redirect(url_for('status', job_id=job_id))


@app.route('/local/v1/instance/<job_id>', methods=['GET'])
def local_status(job_id):
    available = True
    ip = ''
    narupa_status = False
    oci_state = None
    try:
        oci_state, ip, narupa_status = libinstance.check_instance(job_id)
    except Exception as err:
        print(err)
        available = False
    if available and oci_state not in STATES_AVAILABLE:
        available = False
    variables = {
        'ip': ip,
        'narupa_status': narupa_status,
        'available': available,
        'oci_state': oci_state,
    }
    return jsonify(variables)


@app.route('/local/v1/instance/<job_id>', methods=['DELETE'])
def local_terminate(job_id):
    libinstance.terminate_instance(job_id)
    logging.info(f'Terminate instance {job_id}.')
    return jsonify('')


@app.route('/local/v1/instance', methods=['POST'])
def local_launch():
    if ('region' in request.json
            and request.json['region'] != get_current_region()):
        raise BadRequest

    region = request.json.get('region', 'Frankfurt')
    extra_meta = {
        'filename': request.json['simulation'],
        'branch': request.json.get('branch', 'master'),
        'runner': request.json.get('runner', 'ase'),
    }

    try:
        job_id = libinstance.launch_compute_instance(
            region=region, image='git', extra_meta=extra_meta)
    except libinstance.NotEnoughRessources:
        logging.warning(f'Not enough ressources for request {request.json}.')
        return jsonify({'status': NOT_ENOUGH_RESSOURCES})
    except Exception as err:
        logging.error(f'Unexpected error with request {request.json}: {err}.')
        return jsonify({'status': 'failed'})
    
    logging.info(f'Launch {job_id} with request {request.json}.')
    return jsonify({'status': 'success', 'jobid': job_id})


def region_from_job_id(job_id):
    region_string = job_id.split('.')[3]
    return REGION_STRINGS[region_string]


def get_current_region():
    ocid = requests.get('http://169.254.169.254/opc/v1/instance/id').text
    return region_from_job_id(ocid)


@app.route('/api/v1/instance/<job_id>', methods=['GET'])
def api_status(job_id):
    region = region_from_job_id(job_id)
    if region == get_current_region():
        return local_status(job_id)
    if region not in REGIONS:
        raise NotFound
    target = f"{REGIONS[region]['url']}/local/v1/instance/{job_id}"
    return jsonify(requests.get(target).json())

@app.route('/api/v1/instance/<job_id>', methods=['DELETE'])
def api_terminate(job_id):
    region = region_from_job_id(job_id)
    if region == get_current_region():
        return local_terminate(job_id)
    if region not in REGIONS:
        raise NotFound
    logging.info(f'Terminate instance {job_id}.')
    target = f"{REGIONS[region]['url']}/local/v1/instance/{job_id}"
    return jsonify(requests.delete(target).json())


@app.route('/api/v1/instance', methods=['POST'])
def api_launch():
    if not request.is_json:
        raise BadRequest
    region = request.json.get('region', 'Frankfurt')
    if region not in REGIONS:
        logging.warning(f'Bad region in request {request.json}.')
        raise NotFound
    if region == get_current_region():
        return local_launch()
    response = requests.post(
        f"{REGIONS[region]['url']}/local/v1/instance",
        data=json.dumps(request.json),
        headers={"Content-Type": "application/json"},
    )
    response_json = response.json()
    if response_json['status'] == 'success':
        job_id = response_json['jobid']
        logging.info(f'Launch {job_id} with request {request.json}.')
    elif response_json['status'] == NOT_ENOUGH_RESSOURCES:
        logging.warning(f'Not enough ressources for request {request.json}.')
    elif response_json['status'] == 'failed':
        logging.warning(f'Failed to launch request {request.json}.')
    else:
        logging.error(f'Unexpected error with request {request.json}.')

    return jsonify(response_json)
