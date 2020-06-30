import uuid
from datetime import datetime, timedelta


def to_datetime(s):
    return datetime.strptime(s, '%Y-%m-%dT%H:%M:%S')


def datetime_plus_seconds(d, seconds):
    return (d + timedelta(seconds=seconds)).replace(microsecond=0).isoformat()


def now_plus_seconds(seconds):
    return datetime_plus_seconds(datetime.now(), seconds)


def difference_in_minutes(start_at, end_at):
    return (to_datetime(end_at) - to_datetime(start_at)) / timedelta(minutes=1)


def generate_id():
    return str(uuid.uuid4())


def generate_created_at():
    return datetime.now().replace(microsecond=0).isoformat()


def generate_warm_up_at(session):
    return datetime_plus_seconds(to_datetime(session.start_at), -(15 * 60))


def is_dict(d):
    return type(d) is dict


# Taken from https://stackoverflow.com/a/1118038
def to_dict(obj, classkey=None):
    if isinstance(obj, dict):
        data = {}
        for (k, v) in obj.items():
            data[k] = to_dict(v, classkey)
        return data
    elif hasattr(obj, "_ast"):
        return to_dict(obj._ast())
    elif hasattr(obj, "__iter__") and not isinstance(obj, str):
        return [to_dict(v, classkey) for v in obj]
    elif hasattr(obj, "__dict__"):
        data = dict([(key, to_dict(value, classkey))
            for key, value in obj.__dict__.items()
            if not callable(value) and not key.startswith('_')])
        if classkey is not None and hasattr(obj, "__class__"):
            data[classkey] = obj.__class__.__name__
        return data
    else:
        return obj


def pick(d, keys):
    return {k: d.get(k, None) for k in keys}