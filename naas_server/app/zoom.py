import requests
import base64
from . import classes, utils

REDIRECT_URI = 'http://localhost/account'
CLIENT_SECRET = 'vDL54VYjWVUkh2Qemn5EH2cqWnxZWQW8'
CLIENT_ID = 'sJQ6vA2iTNqlIQioeyb7YA'


def init_zoom_tokens(zoom_authorization_code):
    headers = {'Authorization': get_service_auth_header()}
    url = 'https://zoom.us/oauth/token?grant_type=authorization_code&code={}&redirect_uri={}'.format(zoom_authorization_code, REDIRECT_URI)
    json = requests.post(url, headers=headers).json()
    if 'error' in json:
        print(json)
        return None
    json['access_token_expires_at'] = utils.now_plus_seconds(json['expires_in'])
    return classes.UserZoom(json)


def create_meeting(user, session):
    return upsert_meeting(user, session)


def update_meeting(user, session):
    return upsert_meeting(user, session, update=True)


def delete_meeting(user, session):
    auth_header = 'Bearer {}'.format(user.zoom.access_token)
    headers = {'Authorization': auth_header}
    url = 'https://api.zoom.us/v2/meetings/{}'.format(session.zoom_meeting.id)

    requests.delete(url, headers=headers)


def get_service_auth_header():
    encoded_credentials = base64.b64encode('{}:{}'.format(CLIENT_ID, CLIENT_SECRET).encode())
    return 'Basic {}'.format(encoded_credentials.decode())


def refresh_zoom_tokens(user):
    refresh_token = user.zoom.refresh_token
    headers = {'Authorization': get_service_auth_header()}
    url = 'https://zoom.us/oauth/token?grant_type=refresh_token&refresh_token={}'.format(refresh_token)
    json = requests.post(url, headers=headers).json()
    if 'error' in json:
        print(json)
        return None
    json['access_token_expires_at'] = utils.now_plus_seconds(json['expires_in'])
    return classes.UserZoom(json)


def upsert_meeting(user, session, update=False):
    auth_header = 'Bearer {}'.format(user.zoom.access_token)
    headers = {'Authorization': auth_header}
    url = 'https://api.zoom.us/v2'

    start_at = utils.to_datetime(session.start_at)
    end_at = utils.to_datetime(session.end_at)
    duration = int((end_at - start_at).total_seconds() / 60)

    data = {
        'topic': session.simulation.name + ' Narupa session',
        'type': 2,  # scheduled meeting
        'start_time': session.start_at,
        'timezone': session.timezone,
        'duration': duration,
        'password': 'narupa'
    }

    if update:
        url += '/meetings/{}'.format(session.zoom_meeting.id)
        r = requests.patch(url, headers=headers, json=data)
        if r.status_code != 204:
            print(r.status_code)
            return None
        return classes.ZoomMeeting(session.zoom_meeting.to_dict())
    else:
        url += '/users/me/meetings'
        json = requests.post(url, headers=headers, json=data).json()
        if 'error' in json:
            print(json)
            return None
        return classes.ZoomMeeting(json)



