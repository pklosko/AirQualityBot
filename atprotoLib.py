import requests
import time
import datetime
import os
import json

def show_rate_limits(response_headers, request_type=""):
    for header_name, header_value in response_headers.items():
        if "ratelimit" in header_name.lower():
            if header_name.lower() == "ratelimit-reset":
                header_value = datetime.datetime.utcfromtimestamp(int(header_value)).isoformat()
            print(f"{header_name} => {header_value}")

def login(bsky_user, bsky_pass, tcp_delay, token_file=None):
    if token_file and os.path.exists(token_file):
        with open(token_file, "r") as file:
            tokens = json.load(file)
        if get_session(tokens["accessJwt"], tcp_delay) == bsky_user:
            print("getSession OK")
            return tokens["accessJwt"]
        else:
            print("refreshToken")
            new_token = refresh_session(tokens["refreshJwt"], tcp_delay, token_file)
            if new_token:
                return new_token

    print("Go to login")
    url = "https://bsky.social/xrpc/com.atproto.server.createSession"
    data = json.dumps({
        "identifier": bsky_user,
        "password": bsky_pass
    })
    response = requests.post(url, data=data, headers={"Content-Type": "application/json"})
    
    if response.status_code == 200:
        token_data = response.json()
        if token_file:
            with open(token_file, "w") as file:
                json.dump(token_data, file)
        return token_data.get("accessJwt")
    return None

def get_session(token, tcp_delay):
    url = "https://bsky.social/xrpc/com.atproto.server.getSession"
    response = requests.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=tcp_delay / 1000)
  
    if response.status_code == 200:
        return response.json().get("handle")
    return None


def refresh_session(token, tcp_delay, token_file=None):
    url = "https://bsky.social/xrpc/com.atproto.server.refreshSession"
    response = requests.post(url, headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})

    if response.status_code == 200:
        token_data = response.json()
        if token_file:
            with open(token_file, "w") as file:
                json.dump(token_data, file)
        return token_data.get("accessJwt")
    return None

def get_follows(token, bsky_user, tcp_delay, public_ep=False):
    url = f"{'https://public.api.bsky.app' if public_ep else 'https://bsky.social'}/xrpc/app.bsky.graph.getFollows?actor={bsky_user}&limit=100"
    response = get_request(url, token, tcp_delay, "getFollows", public_ep)
    return response.get("follows", []) if response else []

def get_followers(token, bsky_user, tcp_delay, public_ep=False):
    url = f"{'https://public.api.bsky.app' if public_ep else 'https://bsky.social'}/xrpc/app.bsky.graph.getFollowers?actor={bsky_user}"
    response = get_request(url, token, tcp_delay, "getFollowers", public_ep)
    return response.get("followers", []) if response else []

def get_posts(token, actor_did, limit=50, tcp_delay=5000, public_ep=False):
    url = f"{'https://public.api.bsky.app' if public_ep else 'https://bsky.social'}/xrpc/app.bsky.feed.getAuthorFeed?actor={actor_did}&limit={limit}&filter=posts_with_replies"
    response = get_request(url, token, tcp_delay, "getAuthorFeed", public_ep)
    return response.get("feed", []) if response else []

def repost_post(token, bsky_user, post_uri, cid, tcp_delay):
    url = "https://bsky.social/xrpc/com.atproto.repo.createRecord"
    data = {
        "repo": bsky_user,
        "collection": "app.bsky.feed.repost",
        "record": {
            "subject": {"uri": post_uri, "cid": cid},
            "createdAt": datetime.datetime.utcnow().isoformat() + "Z"
        }
    }
    return post_request(url, data, tcp_delay, "createRecord", token)

def post(token, data, tcp_delay):
    url = "https://bsky.social/xrpc/com.atproto.repo.createRecord"
    response = post_request(url, data, tcp_delay, "createRecord", token)
    return response.get("validationStatus", []) if response else []

def get_request(url, token, tcp_delay=5000, request_type="", public_ep=False):
    headers = {"Connection": "close"}
    if not public_ep and token:
        headers["Authorization"] = f"Bearer {token}"
    
    try:
        response = requests.get(url, headers=headers, timeout=tcp_delay / 1000)
        response.raise_for_status()
        show_rate_limits(response.headers, request_type)
        return response.json()
    except requests.RequestException as e:
        print(f"HTTP Request Error: {e}")
        return None

def post_request(url, data, tcp_delay=5000, request_type="", token=None):
    headers = {"Content-Type": "application/json", "Connection": "close"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=tcp_delay / 1000)
        response.raise_for_status()
        show_rate_limits(response.headers, request_type)
        return response.json()
    except requests.RequestException as e:
        print(f"HTTP Request Error: {e}")
        return None

def upload_image(token, filename, tcp_delay, request_type=""):
    url = "https://bsky.social/xrpc/com.atproto.repo.uploadBlob"
    
    # Open the image file in binary read mode
    with open(filename, 'rb') as f:
        # Read the file content
        file_data = f.read()
    
    # Set the headers with the token if provided
    headers = {
        "Content-Type": "image/png"
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    # Prepare the files payload
    files = {'file': (filename, file_data, 'image/png')}
    
    # Send the request
    try:
        response = requests.post(url, headers=headers, data=file_data, timeout=tcp_delay)
        response.raise_for_status()  # Raise an exception for 4xx/5xx responses

        # If the request is successful, return the response JSON
        response_data = response.json()
        show_rate_limits(response.headers, request_type)
        return response_data

    except requests.RequestException as e:
        print(f"Request error: {e}")
        return []
