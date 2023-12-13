import requests


def create_room(endpoint, token=None, scene_name=None, scene_id=None):
    payload = {}
    if scene_id:
        payload = {
            "hub": {
                "name": scene_name,
                "scene_id": scene_id
            }
        }

    headers = {}
    if token:
        headers = {
            "content-type": "application/json",
            "authorization": f'Bearer {token}'
        }

    import json
    body = json.dumps(payload)

    url = f'{endpoint}/api/v1/hubs'
    resp = requests.post(url, body, headers=headers)

    return resp.json()


def upload_media(endpoint, file):
    resp = requests.post(f'{endpoint}/api/v1/media', files={'media': (
        'glb', file, 'application/octet-stream')}, verify=False)
    json = resp.json()

    json = resp.json()
    if "error" in json:
        raise Exception(f'Unknown error')

    return {
        "file_id": json.get("file_id"),
        "access_token": json.get("meta").get("access_token")
    }


def publish_scene(endpoint, token, scene_data, scene_id=None):
    headers = {
        "content-type": "application/json",
        "authorization": f'Bearer {token}'
    }

    import json
    body = json.dumps({"scene": scene_data})

    url = f'{endpoint}/api/v1/scenes{"/" + scene_id if scene_id else ""}'
    if scene_id:
        resp = requests.put(url, body, headers=headers)
    else:
        resp = requests.post(url, body, headers=headers)

    json = resp.json()
    if "error" in json:
        error = json.get("error")
        if error == "invalid_token":
            raise Exception("Authentication error")
        else:
            raise Exception(f'Unknown error: {error}')

    return json


def get_projects(endpoint, token):
    headers = {
        "content-type": "application/json",
        "authorization": f'Bearer {token}'
    }

    resp = requests.get(
        f'{endpoint}/api/v1/scenes/projectless', headers=headers)

    import json
    json = resp.json()
    if "error" in json:
        error = json.get("error")
        if error == "invalid_token":
            raise Exception("Authentication error")
        else:
            raise Exception(f'Unknown error: {error}')

    if "scenes" not in json:
        raise Exception(f'Projects request error')
    scenes = json.get("scenes")
    return scenes
