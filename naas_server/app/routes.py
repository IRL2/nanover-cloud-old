import datetime
import uuid
from flask import render_template, url_for, redirect
from app import app

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html', launch_url=url_for('launch'))


@app.route('/launch')
def launch():
    job_id = uuid.uuid4()
    return redirect(url_for('status', job_id=job_id))


@app.route('/status/<job_id>')
def status(job_id):
    variables = {
        'now': str(datetime.datetime.now()),
        'job_id': job_id,
    }
    return render_template('status.html', **variables)
