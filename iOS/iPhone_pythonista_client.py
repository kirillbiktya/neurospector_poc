from manualCam import *
from dataSender import sendPhoto, sendPhotoLocation
from time import time, sleep
import location


# @on_main_thread
def main():
    location.start_updates()
    print('waiting when accuracy < 10m...')
    while location.get_location()['horizontal_accuracy'] > 10.:
        print(location.get_location()['horizontal_accuracy'])
        sleep(1)
    print(location.get_location())

    focusPosition = 0.78

    try:
        while True:
            imagefilePath = str(time()) + '.jpg'
            print('image_name: ', imagefilePath)
            _time = time()
            print('time:', _time)
            manualCapture(
                AVCaptureVideoOrientationLandscapeRight,
                None, None, None, None,
                AVCaptureFocusModeLocked, focusPosition, None,
                [AVCaptureTorchModeOff, 0.01], imagefilePath,
                'neurospector'
            )
            loc = location.get_location()
            print('location:', loc)

            # send data to server here
            uid = sendPhoto("http://192.168.1.2:3000/upload_photo", imagefilePath)
            sendPhotoLocation("http://172.20.10.12:3000/define_location_for_photo", uid, loc)
    except KeyboardInterrupt:
        location.stop_updates()
        return


main()
