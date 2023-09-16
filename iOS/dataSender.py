import requests
import base64


def sendPhoto(url, image_filename):
    with open(image_filename, 'rb') as f:
        image = f.read()

    r = requests.post(url, files={'photo': image})
    if r.status_code == 200:
        return r.json()['photo_id']
    else:
        print(r.text)
        raise Exception('watafuk')


def sendPhotoLocation(url, photo_id, location):
    data = {'photo_id': photo_id, 'location': location}
    r = requests.post(url, json=data)
    if r.status_code == 200:
        return
    else:
        print(r.text)
        raise Exception('watafuk')