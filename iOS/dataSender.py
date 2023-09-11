import requests
import base64

def sendData(url, image_filename, location):
    with open(image_filename, 'rb') as f:
        image = f.read()
    data = {"image": str(base64.encode(image)), "location": location}

    r = requests.post(url, json=data)
    if r.status_code == 200:
        return
    else:
        print(r.text)
        raise Exception("watafuk")