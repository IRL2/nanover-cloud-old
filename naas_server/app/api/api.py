import os
import logging
from . import zoom, classes, utils, gitlab, gcp
from flask import request
from flask_apscheduler import APScheduler
import firebase_admin
from firebase_admin import auth as firebase_auth, credentials as firebase_credentials, firestore


def init(app):

    scheduler = APScheduler()
    if (not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true') and os.environ.get('NARUPA_SCHEDULER'):
        scheduler.init_app(app)
        scheduler.api_enabled = True
        scheduler.start()
        logging.getLogger('apscheduler').setLevel(logging.WARNING)

    firebase_admin.initialize_app(firebase_credentials.Certificate(os.environ.get('FIREBASE_CREDENTIALS_PATH')))
    db = firestore.client()

    @scheduler.task('cron', id='narupa_scheduler', minute='*')
    @app.route('/api/narupa-scheduler')
    def narupa_scheduler():
        docs = db.collection('sessions').where('instance.status', 'in', ['LAUNCHED', 'WARMING', 'PENDING']).stream()
        for doc in docs:
            try:
                session = classes.Session(doc)
                if session.instance.status == 'PENDING':
                    warm_up(session)
                elif session.instance.status == 'WARMING':
                    warm_up_check(session)
                elif session.instance.status == 'LAUNCHED':
                    launched_check(session)
            except Exception as e:
                app.logger.warning('Unable to run scheduled task on session: {}, with error: {}'.format(doc.id, e))
                app.logger.exception(e)

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
            return unauthorized()
        return user.to_dict()

    @app.route('/api/users/me/zoom', methods=['PUT'])
    def put_users_me_zoom():
        user = get_user_from_request(request)
        if user is None:
            return unauthorized()

        zoom_authorization_code = request.json['zoom_authorization_code']
        zoom_redirect_uri = request.json['zoom_redirect_uri']
        user.zoom = zoom.init_zoom_tokens(zoom_authorization_code, zoom_redirect_uri)
        db_document('users', user.id).set(user.to_dict())
        return no_content()

    @app.route('/api/sessions')
    def get_sessions():
        user = get_user_from_request(request)
        if user is None:
            return unauthorized()

        sessions = []
        docs = db.collection('sessions').where('user_id', '==', user.id).order_by('start_at', direction=firestore.Query.DESCENDING).stream()
        for doc in docs:
            sessions.append(classes.Session(doc).to_dict())
        return {'items': sessions}

    @app.route('/api/sessions/<session_id>')
    def get_session(session_id):
        user = get_user_from_request(request)
        if user is None:
            return unauthorized()

        doc = db_document('sessions', session_id).get()
        session = classes.Session(doc)
        if session.user_id != user.id:
            return unauthorized()

        return session.to_dict()

    @app.route('/api/sessions', methods=['POST'])
    def create_session():
        user = get_user_from_request(request)
        if user is None:
            return unauthorized()

        body = request.json
        session = classes.Session(utils.pick(body, classes.Session.public_fields))
        session.user_id = user.id

        if not session.location:
            return bad_request('Location is required')

        if utils.difference_in_minutes(session.start_at, session.end_at) > 300:
            return bad_request('Session is longer than 5 hour limit')

        if not gitlab.has_branch('11262591', session.branch):
            return bad_request('Invalid branch')

        simulation = db_document('simulations', body['simulation']['id']).get()
        if not simulation.exists:
            return bad_request('Invalid simulation')
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
            return unauthorized()

        doc = db_document('sessions', session_id)
        session = classes.Session(doc.get())
        if session.user_id != user.id:
            return unauthorized()

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
            return unauthorized()

        doc = db_document('sessions', session_id)
        session = classes.Session(doc.get())
        if session.user_id != user.id:
            return unauthorized()

        doc.delete()

        refresh_zoom_tokens(user)
        if session.zoom_meeting and user.has_zoom():
            zoom.delete_meeting(user, session)

        return no_content()

    @app.route('/api/sessions/<session_id>/instance', methods=['DELETE'])
    def delete_session_instance(session_id):
        user = get_user_from_request(request)
        if user is None:
            return unauthorized()

        doc = db_document('sessions', session_id)
        session = classes.Session(doc.get())
        if session.user_id != user.id:
            return unauthorized()

        try:
            gcp.delete_instance(session.location, session.instance.id)
        except Exception as e:
            app.logger.warning('Unable to delete instance for session: {}, with error: {}'.format(doc.id, e))

        session.instance.status = 'STOPPED'
        session.instance.ip = None

        doc.set(session.to_dict())

        return no_content()

    @app.route('/api/simulations')
    def get_simulations():
        user = get_user_from_request(request)
        if user is None:
            return unauthorized()

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
            return unauthorized()

        doc = db_document('simulations', simulation_id).get()
        simulation = classes.Simulation(doc)

        if not simulation.public and simulation.user_id != user.id:
            return unauthorized()

        return simulation.to_dict()

    @app.route('/api/simulations', methods=['POST'])
    def create_simulation():
        user = get_user_from_request(request)
        if user is None:
            return unauthorized()

        simulation = classes.Simulation(utils.pick(request.json, classes.Simulation.public_fields))
        simulation.user_id = user.id

        if not simulation.name:
            return bad_request('Name is required')

        if not simulation.runner:
            return bad_request('Runner is required')

        if simulation.public and not user.can_make_simulations_public:
            return bad_request('You do not have permission to make this simulation public')

        db_document('simulations', simulation.id).set(simulation.to_dict())
        return simulation.to_dict()

    @app.route('/api/simulations/<simulation_id>', methods=['PUT'])
    def update_simulation(simulation_id):
        user = get_user_from_request(request)
        if user is None:
            return unauthorized()

        simulation = classes.Simulation(db_document('simulations', simulation_id).get())

        if simulation.user_id != user.id:
            return bad_request('You do not have permission to update this simulation')

        updates = utils.pick(request.json, classes.Simulation.public_fields)

        if updates['public'] and not user.can_make_simulations_public:
            return bad_request('You do not have permission to make this simulation public')

        db_document('simulations', simulation_id).update(updates)
        return no_content()

    @app.route('/api/simulations/<simulation_id>', methods=['DELETE'])
    def delete_simulation(simulation_id):
        user = get_user_from_request(request)
        if user is None:
            return unauthorized()

        simulation = classes.Simulation(db_document('simulations', simulation_id).get())
        if simulation.user_id != user.id:
            return bad_request('You do not have permission to update this simulation')

        db_document('simulations', simulation_id).delete()
        return no_content()

    @app.route('/', defaults={'path': ''})
    @app.route('/<path>')
    def catch_all(path):
        public_files = ['index.html', 'favicon.ico']
        f = path if path in public_files else 'index.html'
        return app.send_static_file(f)

    def get_user_from_request(req):
        if 'x-narupa-id-token' not in req.headers:
            return None

        try:
            id_token = req.headers['x-narupa-id-token']
            decoded_token = firebase_auth.verify_id_token(id_token)
            uid = decoded_token['uid']
            docs = db.collection('users').where('firebase_uid', '==', uid).stream()
            for doc in docs:
                return classes.User(doc)
            
            app.logger.info('No user found with firebase_ui: {}'.format(uid))
            return None
        except Exception as e:
            app.logger.warning('Unable to get user from request: {}'.format(e))
            return None

    def no_content():
        return '', 204

    def bad_request(message):
        return {'message': message}, 400

    def unauthorized():
        return {'message': 'Unauthorized'}, 401

    def db_document(collection, document_id):
        return db.collection(collection).document(document_id)

    def refresh_zoom_tokens(user):
        if user.has_zoom() and user.zoom.has_access_token_expired():
            user.zoom = zoom.refresh_zoom_tokens(user)
            user_doc = db_document('users', user.id)
            user_doc.set(user.to_dict()) if user.has_zoom() else user_doc.update({'zoom': firestore.DELETE_FIELD})

    def warm_up(session):
        if session.has_warm_up_at_passed():
            runner = session.simulation.runner
            simulation = None
            topology = None
            trajectory = None
            if runner == 'ase' or runner == 'omm':
                simulation = session.simulation.config_url
            elif runner == 'static':
                topology = session.simulation.topology_url
            elif runner == 'trajectory':
                topology = session.simulation.topology_url
                trajectory = session.simulation.trajectory_url

            duration = int(utils.difference_in_seconds(session.warm_up_at, session.end_at))

            try:
                response = gcp.create_instance(session.location, session.branch, runner, duration, end_time=session.end_at, simulation=simulation, topology=topology, trajectory=trajectory)

                if response['status'] in ['PROVISIONING', 'STAGING', 'RUNNING']:
                    session.instance.status = 'WARMING'
                    session.instance.id = response['instanceName']
                else:
                    app.logger.warning('Marking instance as failed in state: ' + response['status'])
                    session.instance.status = 'FAILED'
            except Exception as e:
                app.logger.warning('Failed to create instance: {}'.format(e))
                session.instance.status = 'FAILED'

            db_document('sessions', session.id).set(session.to_dict())

    def warm_up_check(session):
        response = gcp.get_instance(session.location, session.instance.id)
        if response['narupaStatus']:
            session.instance.status = 'LAUNCHED'
            session.instance.ip = response['instanceIp']
            db_document('sessions', session.id).set(session.to_dict())
        elif response['status'] not in ['PROVISIONING', 'STAGING', 'RUNNING']:
            app.logger.warning('Marking instance as failed in state: ' + response['status'])
            session.instance.status = 'FAILED'
            db_document('sessions', session.id).set(session.to_dict())

    def launched_check(session):
        response = gcp.get_instance(session.location, session.instance.id)
        if not response['narupaStatus']:
            session.instance.status = 'STOPPED'
            session.instance.ip = None
            db_document('sessions', session.id).set(session.to_dict())
