#!/usr/bin/env python

from datetime import datetime, timedelta
import pytz
import sys


def minutes_until(target: str, timezone: str, format:str = '%Y-%m-%dT%H:%M:%S'):
    """
    The number of minutes between now and a given date and time.

    The date and time are given as a string in the given format.
    Assuming UTC.
    """
    record_timezone = pytz.timezone(timezone)
    now = datetime.now(pytz.utc)
    target_datetime = datetime.strptime(target, format)
    target_datetime_utc = record_timezone.localize(target_datetime)
    delta = target_datetime_utc - now
    minutes = delta / timedelta(minutes=1)
    return minutes


if __name__ == '__main__':
    try:
        target = sys.argv[1]
        timezone = sys.argv[2]
    except IndexError:
        print(f'Usage: {sys.argv[0]} DATETIME TIMEZONE', file=sys.stderr)
        sys.exit(1)
    print(f'{int(minutes_until(target, timezone))}m')
