import json
import aiohttp
from aiohttp.web import Response

def json_resp(json_data, status=200):
    return Response(body=json.dumps(json_data.copy()), headers={'content-type': 'application/json'}, status=status)

def data_resp(raw_data, status=200):
    return Response(body=raw_data, status=status)

def empty_resp(status=200):
    return Response(body=aiohttp.streams.EmptyStreamReader(), status=status)

