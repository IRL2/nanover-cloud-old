import requests
import urllib


def has_branch(project_id, branch):
    escape_branch = urllib.parse.quote(branch, safe='')
    url = f'https://gitlab.com/api/v4/projects/{project_id}/repository/branches/{escape_branch}'
    response = requests.get(url)
    return response.status_code == requests.codes.ok
