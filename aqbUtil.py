import requests
import os

def getAQdata(url):
  response = requests.get(url)
  if response.status_code == 200:
    return response.json()
  return None


def getImg(url, imgFile):
  response = requests.get(url)
  if response.status_code == 200:
    with open(imgFile, "wb") as file:
      file.write(response.content)
    return os.path.getsize(imgFile)
  return None

def decrypt_str(s):
  dec = ""
  for i in range(len(s)):
    dec += chr(ord(s[i]) - (i % 3))
  return dec
 
def add_tags_to_data(text, location, alert, data, tags):
  index = 0
  tags[f"#{location}"] = [0, 0] 
  for tag, offset in tags.items():
    if tag in text:
      offs = offset[1] if alert else offset[0]
      byte_start = text.find(tag) + offs
      byte_end = byte_start + len(tag)
      facet = {
        'index': {
          'byteStart': byte_start,
          'byteEnd': byte_end
        },
        'features': [
          {
            '$type': 'app.bsky.richtext.facet#tag',
            'tag': tag.replace("#", "")
          }
        ]
      }
      data['record']['facets'].append(facet)
      index += 1
  return data
  
def add_urls_to_data(text, location, alert, data, urls):
  index = 0
  location = decrypt_str(location)
  for url, offset in urls.items():
    if url in text:
      offs = offset[1] if alert else offset[0]
      byte_start = text.find(url) + offs
      byte_end = byte_start + len(url)
      facet = {
        'index': {
          'byteStart': byte_start,
          'byteEnd': byte_end
        },
        'features': [
          {
            '$type': 'app.bsky.richtext.facet#link',
            'uri': f"https://{url}?{location}{offset[2]}"
          }
        ]
      }
      data['record']['facets'].append(facet)
      index += 1
  return data
