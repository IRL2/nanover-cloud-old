import requests
import urllib


def list_branches(project_id):
    json = requests.get('https://gitlab.com/api/v4/projects/{}/repository/branches'.format(project_id)).json()
    return list(map(lambda d: d['name'], json))


def has_branch(project_id, branch):
    escape_branch = urllib.parse.quote(branch, safe='')
    url = f'https://gitlab.com/api/v4/projects/{project_id}/repository/branches/{escape_branch}'
    response = requests.get(url)
    return response.status_code == requests.codes.ok

