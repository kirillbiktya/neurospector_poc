from flask import Flask, request
import uuid
from .database import Database
from .utils import undistort_photo
from config import PHOTO_SAVE_PATH

app = Flask("neurospector_backend")


@app.route("/upload_photo", methods=['POST'])
def upload_photo():
    if request.method == 'POST':
        if "timestamp" in request.args.keys():
            timestamp = request.args["timestamp"]
            f = request.files['photo']
            uid = uuid.uuid4().hex
            file_path = PHOTO_SAVE_PATH + uid + '.jpg'
            f.save(file_path)

            # undistort_photo(file_path)

            db = Database()
            db.add_photo(uid, file_path, timestamp)
            del db

            return {'photo_id': uid}


@app.route("/define_location_for_photo", methods=['POST'])
def new_data():
    if request.method == 'POST':
        db = Database()
        data = request.json
        db.add_location_to_photo(data['photo_id'], data['location'])
        del db

        return {"status": "ok"}
