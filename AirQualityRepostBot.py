#!/usr/bin/python3


import time
import random
import atprotoLib
from dateutil import parser

repost_period = 14400
tcp_delay     = 5000
token         = None
public_ep     = True
posts_limit   = 20

hashtag_arr = [
    "#AirQuality",
    "#AirQualityBot",
    "#Feinstaub",
    "#KvalitaOvzduší",
    "#KvalitaVzduchu",
    "@airqbot.klosko.net"
]

bsky_user  = "airqbot.klosko.net"
bsky_pass  = "Generete unique pass at https://bsky.app/settings/app-passwords"
token_file = "/path/to/tokens.json"

ts = int(time.time())

def strposa(haystack: str, needles: list, offset: int = 0) -> bool:
    haystack = haystack.lower()
    for needle in needles:
        if haystack.find(needle.lower(), offset) != -1:
            return True
    return False

# Get followers
followers = atprotoLib.get_followers(token, bsky_user, tcp_delay, public_ep)
if not followers:
    print("No followers found")
    exit()

# Iterate through followers
for follower in followers:
    actor_did = follower["did"]
    time.sleep(random.randint(3, 7))
    print(f"Proceed posts from @{follower['handle']}")
    
    posts = atprotoLib.get_posts(token, actor_did, posts_limit, tcp_delay, public_ep)
    if not posts:
        print(f"No posts from {follower['handle']} found")
    else:
        for post in posts:
            content = post["post"]["record"]["text"]
            post_uri = post["post"]["uri"]
            cid = post["post"]["cid"]
            try:
                created_at = parser.isoparse(post["post"]["record"]["createdAt"])
                timestamp = int(created_at.timestamp())
            except ValueError as e:
              print("err")
            time_diff = ts - timestamp
            
            if time_diff <= repost_period and strposa(content, hashtag_arr):
                if not token:
                    time.sleep(random.randint(1, 3))
                    token = atprotoLib.login(bsky_user, bsky_pass, tcp_delay, token_file)
                
                if not token:
                    print("Auth Error")
                    exit()
                
                repost_response = atprotoLib.repost_post(token, bsky_user, post_uri, cid, tcp_delay)
                print(f"Repost: @{follower['handle']} : {content}")
