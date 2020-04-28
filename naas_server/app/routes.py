import datetime
import uuid
import oci
from . import libinstance
from flask import render_template, url_for, redirect
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


@app.route('/launch', defaults={'filename': None})
@app.route('/launch/<filename>')
def launch(filename=None):
    if filename is None:
        filename = DEFAULT_FILENAME
    try:
        job_id = libinstance.launch_compute_instance(filename)
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
    }
    return render_template('status.html', **variables)
