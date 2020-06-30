import requests


def list_branches(project_id):
    json = requests.get('https://gitlab.com/api/v4/projects/{}/repository/branches'.format(project_id)).json()
    return list(map(lambda d: d['name'], json))
