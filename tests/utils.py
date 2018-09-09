import os
import json
import aiohttp
from aiohttp import web

def json_resp(json_data, status=200):
    return web.Response(body=json.dumps(json_data), headers={'content-type': 'application/json'}, status=status)

def data_resp(raw_data, status=200):
    return web.Response(body=raw_data, status=status)

def empty_resp(status=200):
    return web.Response(body=aiohttp.streams.EmptyStreamReader(), status=status)
