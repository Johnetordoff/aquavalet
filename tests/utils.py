import json
from aiohttp import web


def json_resp(json_data, status=200):
    return web.Response(body=json.dumps(json_data), headers={'content-type': 'application/json'}, status=status)

def data_resp(raw_data, status=200):
    return web.Response(body=raw_data, status=status)
