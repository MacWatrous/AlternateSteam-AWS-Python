import boto3
import json
import logging
import os
import requests


logger = logging.getLogger()
logger.setLevel(logging.INFO)


def respond(err, res=None):
    return {
        'statusCode': '400' if err else '200',
        'body': err.message if err else (res),
        'headers': {
            'Content-Type': 'application/json',
        },
    }

def auth(client_id,client_secret):
    grant_type = 'client_credentials'
    body_params = {'grant_type' : grant_type}
    url = 'https://accounts.spotify.com/api/token'
    response=requests.post(url, data=body_params, auth = (client_id, client_secret))
    authObj = response.json()
    return authObj['access_token']

def getUrl(event):
    token = auth(os.environ['CLIENT_ID'],os.environ['CLIENT_SECRET'])
    headers = {'content-type': 'application/json','Authorization': 'Bearer ' + token}
    event = json.loads(event['body'])
    text = event['text']
    if "https://" in text:
        #we have a link
        items = text.split(" ")
        for word in items:
            if "open.spotify" in word:
                urlParts = word.split("/")
    else:
        return None

    spotId = urlParts[len(urlParts)-1]
    if urlParts[len(urlParts)-2] == "album":
        alOrTrack = True
    else:
        alOrTrack = False

    if alOrTrack:
        uri = "https://api.spotify.com/v1/albums/" + spotId
        response = requests.get(uri, headers = headers)
        retAlbum = response.json()
    else:
        uri = "https://api.spotify.com/v1/tracks/" + spotId
        response = requests.get(uri, headers = headers)
        retTrack = response.json()

    if alOrTrack:
        artistName = retAlbum['artists'][0]['name']
        names = artistName.split(" ")
        albumName = retAlbum['name']
        albumNames = albumName.split(" ")
        artistFormattedNameAndAlbum = ""
        for name in names:
            artistFormattedNameAndAlbum += name + "+"
        for i in range(0,len(albumNames)):
            artistFormattedNameAndAlbum += albumNames[i]
            if i <= len(albumNames)-2:
                artistFormattedNameAndAlbum += "+"
        searchURL = "https://itunes.apple.com/search?term=" + artistFormattedNameAndAlbum + "&entity=album"
        response = requests.get(searchURL)
        searchResults = response.json()
        if len(searchResults) == 0:
            return None
        for i in range(0,len(searchResults)):
            if searchResults['results'][i]['collectionExplicitness'] is 'explicit':
                return searchResults['results'][i]['collectionViewUrl']
        return searchResults['results'][0]['collectionViewUrl']

    else:
        artistName = retTrack['artists'][0]['name']
        names = artistName.split(" ")
        albumName = retTrack['name']
        albumNames = albumName.split(" ")
        artistFormattedNameAndAlbum = ""
        for name in names:
            artistFormattedNameAndAlbum += name + "+"
        for i in range(0, len(albumNames)):
            artistFormattedNameAndAlbum += albumNames[i]
            if i <= len(albumNames)-2:
                artistFormattedNameAndAlbum += "+"

        searchURL = "https://itunes.apple.com/search?term=" + artistFormattedNameAndAlbum + "&entity=song"
        response = requests.get(searchURL)
        searchResults = response.json()
        if len(searchResults) == 0:
            return None
        for i in range(0,len(searchResults)):
            if searchResults['results'][i]['collectionExplicitness'] is 'explicit':
                return searchResults['results'][i]['collectionViewUrl']
        return searchResults['results'][0]['collectionViewUrl']

def lambda_handler(event,context):
    itunesURL = getUrl(event)
    if itunesURL is not None:
      url = 'https://api.groupme.com/v3/bots/post'
      headers = {'content-type': 'application/json'}
      payload = {'bot_id' : os.environ['BOT_ID'],'text' : itunesURL}
      requests.post(url,data = json.dumps(payload),headers = headers)
      return respond(None, "success")
    return respond(None, "nothing found")
