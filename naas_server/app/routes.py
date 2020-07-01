import requests
import datetime
import json
import os
import logging
import oci
from . import libinstance, zoom, classes, utils, gitlab
from flask import render_template, url_for, redirect, request, jsonify
from flask_cors import CORS
from flask_apscheduler import APScheduler
from werkzeug.exceptions import BadRequest, NotFound, Unauthorized
from app import app
import firebase_admin
from firebase_admin import auth as firebase_auth
from firebase_admin import credentials as firebase_credentials
from firebase_admin import firestore

START_TIME = datetime.datetime.now()
logging.basicConfig(
    filename=f'{START_TIME:%Y%m%d-%H%M%S}.log',
    level=logging.INFO,
)

CORS(app, resources={r'/api/*': {"origins": ["http://localhost:3000", "http://localhost"]}})
app.config['CORS_HEADERS'] = 'Content-Type'

scheduler = APScheduler()
if os.environ.get('NARUPA_SCHEDULER', False):
    scheduler.init_app(app)
    scheduler.api_enabled = True
    scheduler.start()

firebase_admin.initialize_app(firebase_credentials.Certificate(os.environ.get('FIREBASE_CREDENTIALS_PATH')))
db = firestore.client()

STATES_AVAILABLE = (
    oci.core.models.Instance.LIFECYCLE_STATE_PROVISIONING,
    oci.core.models.Instance.LIFECYCLE_STATE_RUNNING,
)
DEFAULT_FILENAME = 'helen.xml'
REPO_URL = 'https://gitlab.com/intangiblerealities/narupacloud/narupa-cloud-simulation-inputs/-/raw/json/'
MANIFEST = 'https://gitlab.com/intangiblerealities/narupacloud/narupa-cloud-simulation-inputs/-/raw/json/manifest.txt'
REGIONS = {
    'Frankfurt': {'url': 'https://app.narupa.xyz', 'string': 'eu-frankfurt-1'},
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
    meta = dict(**request.form)
    simulation = request.form['simulation']
    simu_data = requests.get(REPO_URL + simulation).json()
    meta.update(simu_data)
    # TODO: Do that more cleanly
    if 'simulation' in simu_data:
        meta['simulation'] = REPO_URL + simu_data['simulation']
    if 'topology' in simu_data:
        meta['topology'] = REPO_URL + simu_data['topology']
    if 'trajectory' in simu_data:
        meta['trajectory'] = REPO_URL + simu_data['trajectory']
    data = json.dumps(meta)
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
    metadata = {}
    try:
        oci_state, ip, narupa_status, metadata = libinstance.check_instance(job_id)
    except Exception as err:
        logging.error(err)
        available = False
    if available and oci_state not in STATES_AVAILABLE:
        available = False
    variables = {
        'ip': ip,
        'narupa_status': narupa_status,
        'available': available,
        'oci_state': oci_state,
        'metadata': metadata,
    }
    return jsonify(variables)


@app.route('/local/v1/instance/<job_id>', methods=['DELETE'])
def local_terminate(job_id):
    libinstance.terminate_instance(job_id)
    logging.info(f'Terminate instance {job_id}.')
    return jsonify('')


@app.route('/local/v1/instance', methods=['POST'])
def local_launch():
    logging.info(f'Request to start session {request.json}.')
    if ('region' in request.json
            and request.json['region'] != get_current_region()):
        raise BadRequest

    region = request.json.get('region', 'Frankfurt')
    extra_meta = dict(**request.json)

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


@scheduler.task('cron', id='warm_up_check', minute='*')
@app.route('/api/warm-up-check')
def warm_up_check():
    docs = db.collection('sessions').where('instance.status', '==', 'WARMING').stream()
    for doc in docs:
        try:
            session = classes.Session(doc)

            target = f"{REGIONS[session.location]['url']}/local/v1/instance/{session.instance.id}"
            response_json = requests.get(target).json()
            state = response_json['status']
            if state in STATES_AVAILABLE:
                session.instance.status = 'LAUNCHED'
                session.instance.ip = response_json['ip']
                db_document('sessions', session.id).set(session.to_dict())
        except Exception as e:
            logging.warning('Unable to check session: {}, with error: {}'.format(doc.id, e))

    return no_content()


@scheduler.task('cron', id='warm_up', minute='*')
@app.route('/api/warm-up')
def warm_up():
    docs = db.collection('sessions').where('instance.status', '==', 'PENDING').stream()
    for doc in docs:
        try:
            session = classes.Session(doc)
            if session.has_warm_up_at_passed():
                meta = {'branch': session.branch}
                runner = session.simulation.runner
                if runner == 'ase' or runner == 'omm':
                    meta['simulation'] = session.simulation.config_url
                if runner == 'static':
                    meta['topology'] = session.simulation.topology_url
                if runner == 'trajectory':
                    meta['topology'] = session.simulation.topology_url
                    meta['trajectory'] = session.simulation.trajectory_url

                response_json = requests.post(
                    f"{REGIONS[session.location]['url']}/local/v1/instance",
                    data=json.dumps(meta),
                    headers={"Content-Type": "application/json"},
                ).json()

                if response_json['status'] == 'success':
                    session.instance.status = 'WARMING'
                    session.instance.id = response_json['jobid']
                else:
                    session.instance.status = 'FAILED'

                db_document('sessions', session.id).set(session.to_dict())
        except Exception as e:
            logging.warning('Unable to warm up session: {}, with error: {}'.format(doc.id, e))
    
    return no_content()


@app.route('/api/users', methods=['POST'])
def create_user():
    data = utils.pick(request.json, classes.User.public_fields)
    user = classes.User(data)
    db_document('users', user.id).set(user.to_dict())
    return user.to_dict()


@app.route('/api/users/me')
def get_users_me():
    user = get_user_from_request(request)
    if user is None:
        raise Unauthorized
    return user.to_dict()


@app.route('/api/users/me/zoom', methods=['PUT'])
def put_users_me_zoom():
    user = get_user_from_request(request)
    if user is None:
        raise Unauthorized

    zoom_authorization_code = request.json['zoom_authorization_code']
    zoom_redirect_uri = request.json['zoom_redirect_uri']
    user.zoom = zoom.init_zoom_tokens(zoom_authorization_code, zoom_redirect_uri)
    db_document('users', user.id).set(user.to_dict())
    return no_content()


@app.route('/api/sessions')
def get_sessions():
    user = get_user_from_request(request)
    if user is None:
        raise Unauthorized

    sessions = []
    docs = db.collection('sessions').where('user_id', '==', user.id).order_by('start_at', direction=firestore.Query.DESCENDING).stream()
    for doc in docs:
        sessions.append(classes.Session(doc).to_dict())
    return {'items': sessions}


@app.route('/api/sessions/<session_id>')
def get_session(session_id):
    user = get_user_from_request(request)
    if user is None:
        raise Unauthorized

    doc = db_document('sessions', session_id).get()
    session = classes.Session(doc)
    if session.user_id != user.id:
        raise Unauthorized

    return session.to_dict()


@app.route('/api/sessions', methods=['POST'])
def create_session():
    user = get_user_from_request(request)
    if user is None:
        raise Unauthorized

    body = request.json
    session = classes.Session(utils.pick(body, classes.Session.public_fields))
    session.user_id = user.id

    if utils.difference_in_minutes(session.start_at, session.end_at) > 120:
        raise BadRequest('Session is longer than 2 hour limit')

    if session.branch not in gitlab.list_branches('19161776'):
        raise BadRequest('Invalid branch')
    
    simulation = db_document('simulations', body['simulation']['id']).get()
    session.simulation = classes.Simulation(simulation)

    session.warm_up_at = utils.generate_warm_up_at(session)
    
    refresh_zoom_tokens(user)
    if session.create_conference and user.has_zoom():
        zoom_meeting = zoom.create_meeting(user, session)
        if zoom_meeting:
            session.zoom_meeting = zoom_meeting

    db_document('sessions', session.id).set(session.to_dict())

    return session.to_dict()


@app.route('/api/sessions/<session_id>', methods=['PUT'])
def update_session(session_id):
    user = get_user_from_request(request)
    if user is None:
        raise Unauthorized

    doc = db_document('sessions', session_id)
    session = classes.Session(doc.get())
    if session.user_id != user.id:
        raise Unauthorized

    updates = utils.pick(request.json, classes.Session.public_fields)
    doc.update(updates)
    session = classes.Session(doc.get())

    session.warm_up_at = utils.generate_warm_up_at(session)
    doc.set(session.to_dict())

    refresh_zoom_tokens(user)
    if session.zoom_meeting and user.has_zoom():
        zoom.update_meeting(user, session)

    return no_content()


@app.route('/api/sessions/<session_id>', methods=['DELETE'])
def delete_session(session_id):
    user = get_user_from_request(request)
    if user is None:
        raise Unauthorized

    doc = db_document('sessions', session_id)
    session = classes.Session(doc.get())
    if session.user_id != user.id:
        raise Unauthorized

    doc.delete()

    refresh_zoom_tokens(user)
    if session.zoom_meeting and user.has_zoom():
        zoom.delete_meeting(user, session)

    return no_content()


@app.route('/api/sessions/<session_id>/instance', methods=['DELETE'])
def delete_session_instance(session_id):
    user = get_user_from_request(request)
    if user is None:
        raise Unauthorized

    doc = db_document('sessions', session_id)
    session = classes.Session(doc.get())
    if session.user_id != user.id:
        raise Unauthorized

    target = f"{REGIONS[session.location]['url']}/local/v1/instance/{session.instance.id}"
    requests.delete(target)
    session.instance.status = 'STOPPED'
    session.instance.ip = None

    doc.set(session.to_dict())

    return no_content()


@app.route('/api/simulations')
def get_simulations():
    user = get_user_from_request(request)
    if user is None:
        raise Unauthorized
    
    simulations = []
    docs = db.collection('simulations').order_by('name', direction=firestore.Query.ASCENDING).stream()
    for doc in docs:
        simulation = classes.Simulation(doc)
        if simulation.public or simulation.user_id == user.id:
            simulations.append(simulation.to_dict())

    return {'items': simulations}


@app.route('/api/simulations/<simulation_id>')
def get_simulation(simulation_id):
    user = get_user_from_request(request)
    if user is None:
        raise Unauthorized

    doc = db_document('simulations', simulation_id).get()
    simulation = classes.Simulation(doc)

    if not simulation.public and simulation.user_id != user.id:
        raise Unauthorized

    return simulation.to_dict()


@app.route('/api/simulations', methods=['POST'])
def create_simulation():
    user = get_user_from_request(request)
    if user is None:
        raise Unauthorized

    simulation = classes.Simulation(utils.pick(request.json, classes.Simulation.public_fields))
    simulation.user_id = user.id

    if simulation.public and not user.can_make_simulations_public:
        raise BadRequest

    db_document('simulations', simulation.id).set(simulation.to_dict())
    return simulation.to_dict()


@app.route('/api/simulations/<simulation_id>', methods=['PUT'])
def update_simulation(simulation_id):
    user = get_user_from_request(request)
    if user is None:
        raise Unauthorized

    simulation = classes.Simulation(db_document('simulations', simulation_id).get())
    if simulation.public and not user.can_make_simulations_public:
        raise BadRequest

    updates = utils.pick(request.json, classes.Simulation.public_fields)
    db_document('simulations', simulation_id).update(updates)
    return no_content()


@app.route('/api/simulations/<simulation_id>', methods=['DELETE'])
def delete_simulation(simulation_id):
    user = get_user_from_request(request)
    if user is None:
        raise Unauthorized

    simulation = classes.Simulation(db_document('simulations', simulation_id).get())
    if simulation.public and not user.can_make_simulations_public:
        raise BadRequest

    db_document('simulations', simulation_id).delete()
    return no_content()


@app.route('/api/stats')
def get_stats():
    user = get_user_from_request(request)
    if user is None or user.can_view_stats is not True:
        raise Unauthorized

    total_minutes = 0
    docs = db.collection('sessions').where('instance.status', '==', 'LAUNCHED').stream()
    for doc in docs:
        session = classes.Session(doc)
        total_minutes += utils.difference_in_minutes(session.start_at, session.end_at)

    return {'total_minutes': total_minutes}


@app.route('/', defaults={'path': ''})
@app.route('/<path>')
def catch_all(path):
    public_files = ['index.html', 'favicon.ico']
    f = path if path in public_files else 'index.html'
    return app.send_static_file(f)


def get_user_from_request(req):
    if 'x-narupa-id-token' not in req.headers:
        return None
    
    id_token = req.headers['x-narupa-id-token']
    decoded_token = firebase_auth.verify_id_token(id_token)
    uid = decoded_token['uid']
    docs = db.collection('users').where('firebase_uid', '==', uid).stream()
    for doc in docs:
        return classes.User(doc)


def no_content():
    return '', 204


def db_document(collection, document_id):
    return db.collection(collection).document(document_id)


def refresh_zoom_tokens(user):
    if user.has_zoom() and user.zoom.has_access_token_expired():
        user.zoom = zoom.refresh_zoom_tokens(user)
        user_doc = db_document('users', user.id)
        user_doc.set(user.to_dict()) if user.has_zoom() else user_doc.update({'zoom': firestore.DELETE_FIELD})
