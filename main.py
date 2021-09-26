import requests
import json
from requests.auth import HTTPBasicAuth
from tinydb import TinyDB, Query
from time import sleep
from datetime import datetime
from os import environ

db = TinyDB('db.json')
Task = Query()

JIRA_TOKEN = environ('JIRA_TOKEN')
JIRA_EMAIL = environ('JIRA_EMAIL')
JIRA_PROJECT = environ('JIRA_PROJECT')
JIRA_DOMAIN = environ('JIRA_DOMAIN')


def auth():
    requests.post(
        'https://api-digit.siberian-hub.ru/v1/module/',
        data={
            'type': 'Инструменты',
            'name': 'jira',
            'description': 'Получение информации о завершенных'
        }
    )

def get_tasks() -> dict:
    auth = HTTPBasicAuth(JIRA_EMAIL, JIRA_TOKEN)
    headers = {
        'Accept': 'application/json'
    }
    response = requests.request(
        'GET',
        f'https://{JIRA_DOMAIN}/rest/api/3/search?jql=project%3D{JIRA_PROJECT}%20AND%20(status%3DDONE)',
        headers=headers,
        auth=auth
    )
    return json.loads(response.text)

def main():
    auth()
    while(True):
        tasks = get_tasks()['issues']
        for task in tasks:
            if db.search(Task.key == task['key']):
                continue
            if not task['fields']['assignee']:
                continue
            created = task['fields']['created'].split('T')[0]
            created = datetime.strptime(created, '%Y-%d-%M')
            resolutiondate = task['fields']['resolutiondate'].split('T')[0]
            resolutiondate = datetime.strptime(resolutiondate, '%Y-%d-%M')
            db.insert({
                'key': task['key'],
                'resolutiondate': task['fields']['resolutiondate'],
                'created': task['fields']['created'],
                'assignee': task['fields']['assignee']['displayName'],
                })
            count = (resolutiondate - created).days
            print(count, task['fields']['assignee']['displayName'])
            if count > 10:
                requests.post(
                f'https://api-digit.siberian-hub.ru/v1/module/jira/send/',
                    data={
                        'username': task['fields']['assignee']['displayName'],
                        'value': -count, 
                    }
                )
                continue
            requests.post(
                f'https://api-digit.siberian-hub.ru/v1/module/jira/send/',
                    data={
                        'username': task['fields']['assignee']['displayName'],
                        'value': 10 if count == 0 else count, 
                    }
                )

        sleep(300)

if __name__ == '__main__':
    main()
