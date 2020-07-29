from . import utils
from datetime import datetime
import pytz
import logging


class Session:
    public_fields = ['description', 'start_at', 'timezone', 'end_at', 'record', 'location', 'branch', 'create_conference']

    def __init__(self, data):
        d = data if utils.is_dict(data) else data.to_dict()
        self.id = utils.generate_id() if utils.is_dict(data) else data.id
        self.created_at = d.get('created_at', utils.generate_created_at())
        self.user_id = d.get('user_id', None)
        self.description = d.get('description', None)
        self.warm_up_at = d.get('warm_up_at', None)
        self.start_at = d.get('start_at', None)
        self.end_at = d.get('end_at', None)
        self.terminate_at = d.get('terminate_at', None)
        self.timezone = d.get('timezone', None)
        self.record = d.get('record', False)
        self.create_conference = d.get('create_conference', False)
        self.location = d.get('location', None)
        self.branch = d.get('branch', None)
        self.instance = Instance(d['instance']) if d.get('instance', None) is not None else Instance({'status': 'PENDING'})
        self.simulation = Simulation(d['simulation']) if d.get('simulation', None) is not None else None
        self.zoom_meeting = ZoomMeeting(d['zoom_meeting']) if d.get('zoom_meeting', None) is not None else None

    def to_dict(self):
        return utils.to_dict(self)

    def has_warm_up_at_passed(self):
        now = datetime.now(pytz.utc)
        timezone = pytz.timezone(self.timezone)
        when_naive = utils.to_datetime(self.warm_up_at)
        when = timezone.localize(when_naive)

        return now > when

    @property
    def end_at_utc(self):
        timezone = pytz.timezone(self.timezone)
        when_naive = utils.to_datetime(self.end_at)
        when_aware = timezone.localize(when_naive)
        when_utc = when_aware.astimezone(pytz.utc)
        return when_utc.strftime('%Y-%m-%dT%H:%M:%S')


class User:
    public_fields = ['name', 'email', 'firebase_uid']
    
    def __init__(self, data):
        d = data if utils.is_dict(data) else data.to_dict()
        self.id = utils.generate_id() if utils.is_dict(data) else data.id
        self.created_at = d.get('created_at', utils.generate_created_at())
        self.name = d.get('name', None)
        self.email = d.get('email', None)
        self.can_make_simulations_public = d.get('can_make_simulations_public', None)
        self.can_view_stats = d.get('can_view_stats', None)
        self.firebase_uid = d.get('firebase_uid', None)
        self.zoom = UserZoom(d['zoom']) if d.get('zoom', None) is not None else None

    def to_dict(self):
        return utils.to_dict(self)

    def has_zoom(self):
        return self.zoom and self.zoom.access_token


class Simulation:
    public_fields = ['name', 'description', 'author', 'citation', 'image_url', 'runner', 'config_url', 'topology_url', 'trajectory_url', 'rendering_url', 'public']

    def __init__(self, data):
        d = data if utils.is_dict(data) else data.to_dict()
        self.id = utils.generate_id() if utils.is_dict(data) else data.id
        self.created_at = d.get('created_at', utils.generate_created_at())
        self.user_id = d.get('user_id', None)
        self.name = d.get('name', None)
        self.description = d.get('description', None)
        self.author = d.get('author', None)
        self.citation = d.get('citation', None)
        self.image_url = d.get('image_url', None)
        self.runner = d.get('runner', None)
        self.config_url = d.get('config_url', None)
        self.topology_url = d.get('topology_url', None)
        self.trajectory_url = d.get('trajectory_url', None)
        self.rendering_url = d.get('rendering_url', None)
        self.public = d.get('public', False)

    def to_dict(self):
        return utils.to_dict(self)


class UserZoom:
    def __init__(self, data):
        if data:
            self.access_token = data.get('access_token', None)
            self.refresh_token = data.get('refresh_token', None)
            self.access_token_expires_at = data.get('access_token_expires_at', None)

    def to_dict(self):
        return utils.to_dict(self)

    def has_access_token_expired(self):
        return datetime.now() > utils.to_datetime(self.access_token_expires_at)


class ZoomMeeting:
    def __init__(self, data):
        if data:
            self.id = data.get('id', None)
            self.join_url = data.get('join_url', None)

    def to_dict(self):
        return utils.to_dict(self)


class Instance:
    def __init__(self, data):
        if data:
            self.status = data.get('status', None)  # PENDING, WARMING, LAUNCHED, FAILED, STOPPED
            self.id = data.get('id', None)
            self.ip = data.get('ip', None)

    def to_dict(self):
        return utils.to_dict(self)
