import urllib.request
import json


def get(url, content_type='application/json'):
    r = urllib.request.Request(url,
                                 headers={'User-Agent': 'Overseer Dashboard'})
    if content_type == 'application/json':
        return json.loads(urllib.request.urlopen(r).read().decode('utf-8'))
    else:
        return urllib.request.urlopen(r).read()


def post(url, post_json):
    req = urllib.request.Request(url,
                                 data=json.dumps(post_json).encode('utf8'),
                                 headers={'content-type': 'application/json'})
    return urllib.request.urlopen(req).read()
