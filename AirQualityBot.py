#!/usr/bin/python3

import requests
import time
import datetime
import random
import json
import os
import sys

import aqbUtil
import atprotoLib

bsky_user  = "Replace with your BlueSky ID/name"
bsky_pass  = "Generete unique pass at https://bsky.app/settings/app-passwords"
token_file = "/path/to/tokens.json"


jsonUrl = "https://url/of/AirQualityData.json"
imgUrl  = "https://url/of/AirQualityData.png"

tcp_delay  = 5000
token      = None

tags = {
    "#AirQmonitor": [0, 0],
    "#PM10": [0, 6],
    "#PM2.5": [2, 8],
    "#AirQuality": [4, 10],
    "#AirPollution": [4, 10],
    "#CitizenScience": [4,10],
    "#AirQualityBot": [4, 10]
}

urls = {
    "tmep.cz/mapa/" : [4, 10, "&utm_source=bsky&utm_medium=AirQualityBot"]
}

try:
  checkAlert = (len(sys.argv) > 1 and sys.argv[1].lower() == "checkalert")
except IndexError:
  checkAlert = False

aqbData = aqbUtil.getAQdata(jsonUrl)

if aqbData:
  for location, params in aqbData.items():
    if params['alert'] == False and checkAlert == True:
      print(f"{location} AlertCheck: Alert {params['alert']} => Skip")
      imgSize = None
    else:
      print(f"{location} DailyReport")
      imgSize = aqbUtil.getImg(imgUrl.replace("%DEV-ID%",params["devID"]), params["devID"] + ".png")
    if imgSize:
      date = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S%z")
# Modify your msg text here
      if params['alert'] == True:
        bskyMsg = f"ALERT!\n\u2757PM10 24h avg EXCEEDED ({round(params['limit'])} µg/m³)\u2757 "
      else:
        bskyMsg = "DAILY REPORT"
      text = f"#AirQmonitor #{location} {bskyMsg} [{date}]\n" \
       f"#PM10 min/max/avg [µg/m³]: {params['pm10']}\n" \
       f"#PM2.5 min/max/avg [µg/m³]: {params['pm2']}\n\n" \
       f"Details: tmep.cz/mapa/\n\n" \
       f"#AirQuality #AirPollution #CitizenScience\n#AirQualityBot"
      data = {
             'repo': bskyUser,
             'collection': 'app.bsky.feed.post',
             'record': {
                       '$type': 'app.bsky.feed.post',
                       'text': text,
                       'facets': [],  # This will be populated later
                       'createdAt': datetime.datetime.utcnow().isoformat() + "Z",  # Current timestamp in required format
                       'embed': {
                                '$type': 'app.bsky.embed.images',
                                'images': []  # No images for now
                                }
                       }
             }
      data = aqbUtil.add_tags_to_data(text, location, params['alert'], data, tags)
      data = aqbUtil.add_urls_to_data(text, params['tzll'], params['alert'], data, urls)

      if not token:
        time.sleep(random.randint(1, 3))
        token = atprotoLib.login(bskyUser, bskyPass, tcp_delay, token_file)
      if not token:
        print("Auth Error")
        os.system(push_notify + " 'Bsky Aurh Error'")
        exit()
      img_json = atprotoLib.upload_image(token, os.path.abspath(params["devID"] + ".png"), tcp_delay, "uploadBlob")
      if not img_json:
        print("Img Upload Error")
      else:
        data_string = json.dumps(data)
        json_data = json.loads(data_string)
        image_data = {
                     'image': img_json['blob'],
                     'alt': f'AirQmonitor {location} AirQuality graph [{date}]',
                     'aspectRatio': {'width': 781, 'height': 343}
                     }
        json_data['record']['embed']['images'].append(image_data)
        data_string = json.dumps(json_data)
        data_string = data_string.replace("\\\\", "\\")
        post = atprotoLib.post(token, json.loads(data_string), tcp_delay)
        if not post:
          print("Post Error")
        else:
          print(f"Post {post}")
