import json
from typing import Union

import urllib3

from leek.api.db.store import Task, Worker, STATES_SUCCESS, STATES_EXCEPTION, STATES_UNREADY
from leek.api.conf import settings


def get_color(state):
    if state in STATES_EXCEPTION:
        return "danger"
    elif state in STATES_SUCCESS:
        return "good"
    elif state in STATES_UNREADY:
        return "#36C5F0"
    else:
        return "yellow"


def send_slack(app_name: str, event: Union[Task, Worker], wh_url: str, extra: dict):
    fields = [
        {
            "title": "Application",
            "value": app_name,
            "short": True,
        },
        {
            "title": "Environment",
            "value": event.app_env,
            "short": True,
        },
        {
            "title": "Task worker",
            "value": event.worker,
            "short": True,
        },
        {
            "title": "Task state",
            "value": event.state,
            "short": True,
        },
        {
            "title": "Task uuid",
            "value": event.uuid,
            "short": False,
        }
    ]
    if extra.get("note"):
        fields.append(
            {
                "title": "Note",
                "value": extra.get("note"),
                "short": False,
            }
        )
    body = {
        "attachments": [
            {
                "color": get_color(event.state),
                "title": f"Task: {event.name}",
                "title_link": f"{settings.LEEK_WEB_URL}/task?app={app_name}&uuid={event.uuid}",
                "fields": fields,
            },
        ],
    }
    http = urllib3.PoolManager()
    try:
        http.request(
            "POST",
            wh_url,
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            body=json.dumps(body)
        )
    except urllib3.exceptions.HTTPError as e:
        print('Request to slack returned an error:', e.reason)
