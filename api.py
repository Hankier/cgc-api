import asyncio
import json
import logging
import time
import sanic
import requests


from cryptography.fernet import Fernet, InvalidToken

from cors import add_cors_headers
from options import setup_options
from db import Database
from config import Config
from scrapper import Scrapper
from opensea import OpenseaAPI
from utils import get_display_time

__author__ = 'Hankier'
__version__ = '0.0.1'
__codename__ = 'Pilot Pirate'

# MAIN CONF
CONF = Config()

APP = sanic.Sanic(CONF.app_name())

START_TIME = time.time()

KEY = Fernet.generate_key()  # store in a secure location
# Add OPTIONS handlers to any route that is missing it
APP.register_listener(setup_options, "before_server_start")
# Fill in CORS headers
APP.register_middleware(add_cors_headers, "response")

logging.basicConfig(
            format='%(asctime)s - %(funcName)s - %(levelname)s - %(message)s',
                level=logging.DEBUG
                )
LOGGER = logging.getLogger(CONF.app_name())

log_file_handler = logging.FileHandler(CONF.app_log_file())
log_file_handler.setLevel(logging.DEBUG)
LOGGER.addHandler(log_file_handler)


DB = Database(CONF.postgres())
OS_API = OpenseaAPI(CONF.opensea_api())




@APP.route('/')
def home(request: sanic.request.Request) -> sanic.response.HTTPResponse:
    """ Return some cool text info about an app. """
    return sanic.response.text('\n'.join([
'  __________      '        + '',
' / ___  ___ \\    '        + '',
'/ / @ \\/ @ \\ \\   '        + f'  apiNFT v{__version__} [{__codename__}]',
'\\ \\___/\\___/ /\\  '        + '',
' \\____\\/____/||   '        + '',
' /     /\\\\\\\\\\//   '        + f'  > Author:  {__author__}',
'|     |\\\\\\\\\\\\     '        + '',
' \\      \\\\\\\\\\\\    '        + '',
'   \\______/\\\\\\\\   '        + '',
'    _||_||_           '    + f'  Uptime: {get_display_time(time.time() - START_TIME, 6)}',
''
]))

@APP.route("/nft", methods=["POST",])
def nft(request):
    LOGGER.debug("nft POST: %s" % request.body)
    content = json.loads(request.body)
    LOGGER.debug(f'user: {content["username"]}')
    return sanic.response.text("nft POST: %s" % request.body)


def encrypt(message: str, key: bytes) -> bytes:
    return Fernet(key).encrypt(message.encode())

def decrypt(token: str, key: bytes) -> bytes:
    return Fernet(key).decrypt(token.encode())

@APP.route("/token", methods=["POST"])
def token(request):
    LOGGER.debug("token POST: %s" % request.body)
    content = json.loads(request.body)
    requestor = content['user']
    token = encrypt(requestor, KEY)
    LOGGER.debug("token: %s" % token.decode())
    return sanic.response.json({"token": token.decode()})

@APP.route("/verify", methods=["POST",])
def token(request):
    LOGGER.debug("verify POST: %s" % request.body)
    content = json.loads(request.body)
    token = content['token']
    try:
        msg = decrypt(token, KEY)
    except InvalidToken:
        return sanic.response.json({"verified": False, "token": token})

    LOGGER.debug("msg: %s" % msg.decode())
    query = "SELECT project_id, name, opensea FROM collections;"
    records = DB.get_rows(query)
    LOGGER.debug("QUERY")
    projects = []
    for row in records:
        projects.append({'id': row['project_id'], 'name': row['name'], 'opensea': row['opensea']})
        LOGGER.debug(row)
    return sanic.response.json({"verified": True, "token": token, "projects": projects})

@APP.route("/projects", methods=["POST"])
def token(request):
    LOGGER.debug("token POST: %s" % request.body)
    content = json.loads(request.body)
    requestor = content['user']
    query = "SELECT project_id, name, opensea FROM collections;"
    records = DB.get_rows(query)
    LOGGER.debug("QUERY")
    projects = []
    for row in records:
        projects.append({'id': row['project_id'], 'name': row['name'], 'opensea': row['opensea']})
        LOGGER.debug(row)
    #result = json.dumps(projects)
    return sanic.response.json({"status_ok": True, "info": "Listing projects", "projects": projects})

@APP.route("/projects-like", methods=["POST"])
def token(request):
    LOGGER.info("token POST: %s" % request.body)
    content = json.loads(request.body)
    requestor = content['user']
    like_param = content['like']
    query = f"SELECT project_id, name, opensea FROM collections WHERE name iLIKE %(like_param)s;"
    params = {'like_param': f'%{like_param}%'}
    LOGGER.info(f"QUERY: {query}")
    records = DB.get_rows(query, params)
    LOGGER.debug("QUERY")
    projects = []
    for row in records:
        projects.append({'id': row['project_id'], 'name': row['name'], 'opensea': row['opensea']})
        LOGGER.info(row)
    #result = json.dumps(projects)
    LOGGER.debug(f"Result: {projects}")
    return sanic.response.json({"status_ok": True, "info": "Listing projects", "projects": projects})

@APP.route("/project-info", methods=["POST"])
def token(request):
    LOGGER.debug("token POST: %s" % request.body)
    content = json.loads(request.body)
    requestor = content['user']
    project = content['project_id']
    query = f'SELECT * FROM collections WHERE project_id = {project};'
    records = DB.get_rows(query)
    data = [dict(row) for row in records]
    LOGGER.debug("QUERY - PRJ")
    LOGGER.debug(data)
    _, _, stats = OS_API.get_collection(data[0]['opensea'])
    return sanic.response.json({"status_ok": True, "info": "project_info", "project": data[0], "opensea": stats})

@APP.route("/project-info-name", methods=["POST"])
def project_info_name(request):
    LOGGER.debug("token POST: %s" % request.body)
    content = json.loads(request.body)
    requestor = content['user']
    project = content['project_name']
    query = f"SELECT * FROM collections WHERE name = '{project}';"
    records = DB.get_rows(query)
    data = [dict(row) for row in records]
    LOGGER.debug("QUERY - PRJ")
    LOGGER.debug(data)
    _, _, stats = OS_API.get_collection(data[0]['opensea'])
    return sanic.response.json({"status_ok": True, "info": "project_info", "project": data[0], "opensea": stats})

@APP.route("/dummy", methods=["POST"])
def token(request):
    LOGGER.debug("dummy POST: %s" % request.body)
    content = json.loads(request.body)
    return sanic.response.json({"status_ok": False, "added": False, "info": "Take it all", "request": content})

@APP.route("/take-all", methods=["POST"])
def token(request):
    LOGGER.debug("dummy POST: %s" % request.body)
    content = json.loads(request.body)
    collection_slug = content['collection']
    query = f"SELECT project_id, name, opensea FROM collections WHERE opensea LIKE %(collection_slug)s"
    params = {'collection_slug': collection_slug}
    records = DB.get_rows(query, params)
    data = [dict(row) for row in records]
    LOGGER.info(records)
    if len(records) == 0:
        status_ok, name, opensea = OS_API.get_collection(collection_slug)
        if status_ok:
            stats = opensea['stats']
            LOGGER.info(f'Collection: {stats}')
            if stats["floor_price"] is None:
                floor = 'NULL'
            else:
                floor = stats["floor_price"]
            diff_volume = 'NULL'
            diff_sales = 'NULL'

            query_add = f'''INSERT INTO collections (name, opensea)
            VALUES ('{name}', '{collection_slug}') RETURNING project_id, name, opensea;'''
            LOGGER.info(f"Wynik: {query_add}")
            added = DB.insert(query_add)
            project_id = added["project_id"]
            LOGGER.info(f'Added {added}')
            LOGGER.info(f'Adtyp {added}')
            data = dict(added)

            query = f'''INSERT INTO stats (collection, supply, sales, total_sales, owners, count, reports, floor, volume, total_volume, date)
            VALUES ({project_id}, {stats["total_supply"]}, {diff_sales}, {stats["total_sales"]}, {stats["num_owners"]}, {stats["count"]}, {stats["num_reports"]}, {floor}, {diff_volume}, {stats["total_volume"]} ,current_timestamp)
            RETURNING *;'''

            records = DB.insert(query)
            LOGGER.info('ADDED')
            return sanic.response.json({"status_ok": True, "added": True, "error": False, "reason": "Collection added.", "request": content, "project": data, "opensea": opensea})
        else:
            LOGGER.info('FAILED CONNETION OS')
            return sanic.response.json({"status_ok": True, "added": False, "error": True, "reason": "Connection to Opensea failed or collection does not exist.", "request": content})
    else:
        status_ok, name, opensea = OS_API.get_collection(collection_slug)
        LOGGER.info('ALREADY EXISTS')
        return sanic.response.json({"status_ok": True, "added": False, "error": False, "reason": "Collection already exists", "request": content, "project": data, "opensea": opensea})


@APP.listener('before_server_start')
async def setup(app, loop):
    """ Initialzie sanic APP before server start. """
    LOGGER.info(f'Key: {KEY.decode()}')
    LOGGER.info('Setup done')


def main(host: str, port: int) -> None:
    APP.run(host=host, port=port, backlog=8192)

if __name__ == '__main__':
    main(host=CONF.app_host(), port=CONF.app_port())
