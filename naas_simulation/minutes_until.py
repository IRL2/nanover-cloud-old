#!/usr/bin/env python

from datetime import datetime, timedelta
import sys


def minutes_until(target: str, format:str = '%Y-%m-%dT%H:%M:%S'):
    """
    The number of minutes between now and a given date and time.

    The date and time are given as a string in the given format.
    Assuming UTC.
    """
    now = datetime.utcnow()
    target_datetime = datetime.strptime(target, format)
    delta = target_datetime - now
    minutes = delta / timedelta(minutes=1)
    return minutes


if __name__ == '__main__':
    try:
        target = sys.argv[1]
    except IndexError:
        print(f'Usage: {sys.argv[0]} DATETIME', file=sys.stderr)
        sys.exit(1)
    print(f'{int(minutes_until(target))}m')
