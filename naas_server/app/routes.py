import datetime
import uuid
import oci
from . import libinstance
from flask import render_template, url_for, redirect, request
from app import app

STATES_AVAILABLE = (
    oci.core.models.Instance.LIFECYCLE_STATE_PROVISIONING,
    oci.core.models.Instance.LIFECYCLE_STATE_RUNNING,
)
DEFAULT_FILENAME = 'helen.xml'


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html', launch_url=url_for('launch'))


@app.route('/isness')
def isness():
    return render_template('index.html', launch_url=url_for('launch', filename='40-ALA.narupa2.xml'))


@app.route('/git')
def git():
    simulation_list = libinstance.list_simulations()
    return render_template(
            'gitindex.html',
            launch_url=url_for('gitlaunch'),
            simulation_list=simulation_list)


@app.route('/launch', defaults={'filename': None, 'image': 'default'})
@app.route('/launch/<filename>', defaults={'image': 'default'})
@app.route('/launch/<filename>/<image>')
def launch(filename=None, image='default'):
    return launch_instance(filename=filename, image=image)


@app.route('/gitlaunch', methods=['POST'])
def gitlaunch():
    return launch_instance(
        #filename='40-ALA.narupa2.xml',
        filename=request.form['simulation'],
        image='git',
        extra_meta={'branch': request.form['narupa_protocol']},
    )


def launch_instance(filename=None, image='default', extra_meta={}):
    if filename is None:
        filename = DEFAULT_FILENAME
    try:
        job_id = libinstance.launch_compute_instance(
                filename, image=image, extra_meta=extra_meta)
    except libinstance.NotEnoughRessources:
        return 'No resource available. Try again later.'
    #except Exception as err:
    #    print(err)
    #    return 'Something unexpected happened.'
    return redirect(url_for('status', job_id=job_id))


@app.route('/status/<job_id>')
def status(job_id):
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
        'terminate_url': url_for('terminate', job_id=job_id),
    }
    return render_template('status.html', **variables)


@app.route('/terminate/<job_id>')
def terminate(job_id):
    libinstance.terminate_instance(job_id)
    return redirect(url_for('status', job_id=job_id))
