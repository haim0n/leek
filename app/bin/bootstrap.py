import json
import logging
import os
import signal
import subprocess
import sys

import requests
import time
from printy import printy
from elasticsearch import Elasticsearch

"""
PRINT APPLICATION HEADER
"""

logging.basicConfig(level="INFO", format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger(__name__)


def abort(msg):
    logger.error(msg)
    os.kill(1, signal.SIGTERM)
    sys.exit(1)


def get_bool(env_name, default="false"):
    return os.environ.get(env_name, default).lower() == "true"


def get_status(b):
    return "[n>]ENABLED@" if b else "[r>]DISABLED@"


LEEK_VERSION = os.environ.get("LEEK_VERSION", "-.-.-")
LEEK_RELEASE_DATE = os.environ.get("LEEK_RELEASE_DATE", "0000/00/00 00:00:00")
LEEK_ENV = os.environ.get("LEEK_ENV", "PROD")
ENABLE_ES = get_bool("LEEK_ENABLE_ES")
ENABLE_API = get_bool("LEEK_ENABLE_API")
ENABLE_AGENT = get_bool("LEEK_ENABLE_AGENT")
ENABLE_WEB = get_bool("LEEK_ENABLE_WEB")
LEEK_ES_URL = os.environ.get("LEEK_ES_URL", "http://0.0.0.0:9200")
LEEK_API_URL = os.environ.get("LEEK_API_URL", "http://0.0.0.0:5000")
LEEK_WEB_URL = os.environ.get("LEEK_WEB_URL", "http://0.0.0.0:8000")
LEEK_API_ENABLE_AUTH = get_bool("LEEK_API_ENABLE_AUTH", default="true")

LOGO = """
8 8888         8 8888888888   8 8888888888   8 8888     ,88'
8 8888         8 8888         8 8888         8 8888    ,88' 
8 8888         8 8888         8 8888         8 8888   ,88'  
8 8888         8 8888         8 8888         8 8888  ,88'   
8 8888         8 888888888888 8 888888888888 8 8888 ,88'    
8 8888         8 8888         8 8888         8 8888 88'     
8 8888         8 8888         8 8888         8 888888<      
8 8888         8 8888         8 8888         8 8888 `Y8.    
8 8888         8 8888         8 8888         8 8888   `Y8.  
8 888888888888 8 888888888888 8 888888888888 8 8888     `Y8.                        
"""
USAGE = f"""
[b>]|#|@     [y>]Leek Celery Monitoring Tool@                               [b>]|#|@
[b>]|#|@     [n>]Versions:@ {LEEK_VERSION}                                  [b>]|#|@
[b>]|#|@     [n>]Release date:@ {LEEK_RELEASE_DATE}                         [b>]|#|@
[b>]|#|@     [n>]Codename:@ Fennec                                          [b>]|#|@
[b>]|#|@     [n>]Repository:@ https://github.com/kodless/leek               [b>]|#|@
[b>]|#|@     [n>]Homepage:@ https://tryleek.com                             [b>]|#|@
[b>]|#|@     [n>]Documentation:@ https://tryleek.com/docs/introduction/leek [b>]|#|@

[r>]Author:@ Hamza Adami <me@adamihamza.com>
[r>]Follow me on Github:@ https://github.com/kodless 
[r>]Buy me a coffee:@ https://buymeacoffee.com/fennec
"""
SERVICES = f"""
[y>]SERVICE     STATUS      URL
=======     ------      ---@
- API       {get_status(ENABLE_API)}    {LEEK_API_URL}
- WEB       {get_status(ENABLE_WEB)}    {LEEK_WEB_URL}
- AGENT     {get_status(ENABLE_AGENT)}    -
"""

printy(LOGO, "n>B")
printy(USAGE)
printy(SERVICES)

"""
ADAPT/VALIDATE VARIABLES
"""

if ENABLE_ES:
    logger.warning("Starting from version 0.4.0 local elasticsearch is deprecated! This is to "
                   "improve leek docker image size.\n"
                   "If you are still interested in local elasticsearch you can use the official "
                   "ES docker image to run a sidecar elasticsearch container.")

# WEB VARIABLES
if ENABLE_WEB:
    if LEEK_API_ENABLE_AUTH is True:
        if LEEK_ENV == "PROD":
            LEEK_FIREBASE_PROJECT_ID = os.environ.get("LEEK_FIREBASE_PROJECT_ID")
            LEEK_FIREBASE_APP_ID = os.environ.get("LEEK_FIREBASE_APP_ID")
            LEEK_FIREBASE_API_KEY = os.environ.get("LEEK_FIREBASE_API_KEY")
            LEEK_FIREBASE_AUTH_DOMAIN = os.environ.get("LEEK_FIREBASE_AUTH_DOMAIN")
            none_fb_prams = [LEEK_FIREBASE_PROJECT_ID, LEEK_FIREBASE_APP_ID, LEEK_FIREBASE_API_KEY,
                             LEEK_FIREBASE_AUTH_DOMAIN].count(None)
            if 1 <= none_fb_prams <= 3:
                abort(
                    "If one of [LEEK_FIREBASE_PROJECT_ID, LEEK_FIREBASE_APP_ID, LEEK_FIREBASE_API_KEY, "
                    "LEEK_FIREBASE_AUTH_DOMAIN] is provided all should be provided, Or if you want to "
                    "use default firebase project do not set any of these env variables"
                )

            if none_fb_prams == 4:
                logger.warning("Using default firebase project for authentication!")

            web_conf = f"""
            window.leek_config = {{
                "LEEK_API_URL": "{LEEK_API_URL}",
                "LEEK_API_ENABLE_AUTH": "true",
                "LEEK_FIREBASE_PROJECT_ID": "{LEEK_FIREBASE_PROJECT_ID or "kodhive-leek"}",
                "LEEK_FIREBASE_APP_ID": "{LEEK_FIREBASE_APP_ID or "1:894368938723:web:e14677d1835ce9bd09e3d6"}",
                "LEEK_FIREBASE_API_KEY": "{LEEK_FIREBASE_API_KEY or "AIzaSyBiv9xF6VjDsv62ufzUb9aFJUreHQaFoDk"}",
                "LEEK_FIREBASE_AUTH_DOMAIN": "{LEEK_FIREBASE_AUTH_DOMAIN or "kodhive-leek.firebaseapp.com"}",
                "LEEK_VERSION": "{LEEK_VERSION}",
            }};
            """

            web_conf_file = "/opt/app/public/leek-config.js"
            with open(web_conf_file, 'w') as f:
                f.write(web_conf)
        else:
            logger.warning("Using default firebase project for authentication!")
    else:
        web_conf = f"""
        window.leek_config = {{
            "LEEK_API_URL": "{LEEK_API_URL}",
            "LEEK_API_ENABLE_AUTH": "false",
            "LEEK_VERSION": "{LEEK_VERSION}",
        }};
        """

        web_conf_file = "/opt/app/public/leek-config.js"
        with open(web_conf_file, 'w') as f:
            f.write(web_conf)


def validate_subscriptions(subs):
    if not isinstance(subs, dict):
        abort(f"Agent subscriptions should be a dict of subscriptions")

    # Validate each subscription
    for subscription_name, subscription in subs.items():
        required_keys = [
            "broker", "exchange", "queue", "routing_key", "org_name",
            "app_name", "app_env",  # "app_key", "api_url"
        ]
        keys = subscription.keys()
        if not all(required_key in keys for required_key in required_keys):
            abort(f"Agent subscription configuration is invalid")

    if ENABLE_API:
        # Agent and API in the same runtime, prepare a shared secret for communication between them
        for subscription_name, subscription in subs.items():
            try:
                subscription["app_key"] = os.environ["LEEK_AGENT_API_SECRET"]
            except KeyError:
                abort("Agent and API are both enabled in same container, LEEK_AGENT_API_SECRET env variable should "
                      "be specified for inter-communication between agent and API")
            # Use local API URL not from LEEK_API_URL env var, LEEK_API_URL is used by Web app (browser)
            subscription["api_url"] = "http://0.0.0.0:5000"

    # Optional settings
    for subscription_name, subscription in subs.items():
        if not subscription.get("concurrency_pool_size"):
            subscription["concurrency_pool_size"] = 1

        if not subscription.get("prefetch_count"):
            subscription["prefetch_count"] = 1000

        if not LEEK_API_ENABLE_AUTH:
            subscription["org_name"] = "mono"
    return subs


# AGENT VARIABLES
if ENABLE_AGENT:
    subscriptions_file = "/opt/app/conf/subscriptions.json"
    subscriptions = os.environ.get("LEEK_AGENT_SUBSCRIPTIONS")
    if subscriptions:
        try:
            subscriptions = json.loads(subscriptions)
        except json.decoder.JSONDecodeError:
            abort("LEEK_AGENT_SUBSCRIPTIONS env var should be a valid json string!")
        subscriptions = validate_subscriptions(subscriptions)
        with open(subscriptions_file, 'w') as f:
            json.dump(subscriptions, f, indent=4, sort_keys=False)
    else:
        with open(subscriptions_file) as s:
            try:
                subscriptions = json.load(s)
            except json.decoder.JSONDecodeError:
                abort("Subscription file should be a valid json file!")
            subscriptions = validate_subscriptions(subscriptions)
        if not len(subscriptions):
            logger.warning(f"LEEK_AGENT_SUBSCRIPTIONS environment variable is not set, and subscriptions file does not "
                           f"declare any subscriptions, Try adding subscriptions statically via env variable or "
                           f"dynamically via agent page {LEEK_WEB_URL}.")
        with open(subscriptions_file, 'w') as f:
            json.dump(subscriptions, f, indent=4, sort_keys=False)

"""
START SERVICES AND ENSURE CONNECTIONS BETWEEN THEM
"""


def create_painless_scripts():
    connection = Elasticsearch(LEEK_ES_URL)
    with open('/opt/app/conf/painless/TaskMerge.groovy', 'r') as script:
        task_merge_source = script.read()

    with open('/opt/app/conf/painless/WorkerMerge.groovy', 'r') as script:
        worker_merge_source = script.read()

    try:
        t = connection.put_script(id="task-merge", body={
            "script": {
                "lang": "painless",
                "source": task_merge_source
            }
        })
        w = connection.put_script(id="worker-merge", body={
            "script": {
                "lang": "painless",
                "source": worker_merge_source
            }
        })
        if t["acknowledged"] is True and w["acknowledged"] is True:
            return
    except Exception:
        pass
    abort(f"Could not create painless scripts!")


def ensure_connection(target):
    for i in range(10):
        try:
            requests.options(url=target).raise_for_status()
            return
        except Exception as e:
            time.sleep(5)
            continue
    abort(f"Could not connect to target {target}")


if ENABLE_API:
    # Make sure ES (whether it is local or external) is up before starting the API.
    ensure_connection(LEEK_ES_URL)
    # Create painless scripts used for merges
    create_painless_scripts()
    # Start API process
    subprocess.run(["supervisorctl", "start", "api"])
    # Make sure the API is up before starting the agent
    ensure_connection(f"{LEEK_API_URL}/v1/events/process")

if ENABLE_AGENT:
    # Start agent.
    # If you don't have access to brokers infrastructure, you can setup standalone agent on third party infra
    subprocess.run(["supervisorctl", "start", "agent"])

if ENABLE_WEB:
    # Start web application
    # If you don't want to spin up the web with the same runtime as API, you can deploy it on a cdn like Netlify
    subprocess.run(["supervisorctl", "start", "web"])
