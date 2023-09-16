import cv2
import numpy as np
from .database import Database


camera_matrix = np.array([[5.50760229e+03, 0.00000000e+00, 5.46676429e+02],
                          [0.00000000e+00, 5.47150146e+03, 5.51231057e+02],
                          [0.00000000e+00, 0.00000000e+00, 1.00000000e+00]])
dist_coefs = np.array([3.57015094e+00, -2.95471127e+02, 7.48611524e-02,  6.15119781e-03, 7.90089689e+03])
# camera_matrix_wide = np.array([[2.26832210e+03, 0.00000000e+00, 5.45585764e+02],
#                           [0.00000000e+00, 2.28453885e+03, 5.86199590e+02],
#                           [0.00000000e+00, 0.00000000e+00, 1.00000000e+00]])
# dist_coefs_wide = np.array([4.64355432e-01, -8.53787341e+00, -1.13059232e-03, 1.16034398e-02, 3.71906128e+01])


def undistort_photo(path):
    img = cv2.imread(path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    h, w = img.shape[:2]
    newcameramtx, roi = cv2.getOptimalNewCameraMatrix(camera_matrix, dist_coefs, (w, h), 1, (w, h))
    dst = cv2.undistort(img, camera_matrix, dist_coefs, None, newcameramtx)
    dst = cv2.cvtColor(dst, cv2.COLOR_BGR2RGB)
    cv2.imwrite(path, dst)


def get_fov(imsize, aperture_width=1.8, aperture_height=26):
    return cv2.calibrationMatrixValues(camera_matrix, imsize, aperture_width, aperture_height)


def get_fov_i11(im_size):
    if im_size.width < im_size.height:
        d = 4.3
    else:
        d = 5.8

    fov = np.rad2deg(2 * np.arctan(d / (2 * 26 / 6.03)))

    return fov


def meters_to_lat_grad(meters):
    return meters / 111134.861111


def meters_to_lon_grad(meters, latitude):
    return meters / (np.cos(latitude) * 111321.377778)


def get_line_coords_from_vector(vector_uid, length):
    db = Database(db_name='C:/Users/Kirill/PycharmProjects/neurospector_backend/database.sqlite')
    vector = db.get_vector(vector_uid)
    location = db.get_location(vector[0]['photo_uid'])
    detection = db.get_detection(vector[0]['detection_uid'])
    angle = np.deg2rad(detection[0]['angle'])

    start_position = {
        'lat': location[0]['latitude'], 'lon': location[0]['longitude'], 'uid': vector[0]['detection_uid'],
        'type': 'start'
    }
    end_lat = location[0]['latitude'] + meters_to_lat_grad(length) * np.sin(angle)
    end_lon = location[0]['longitude'] + meters_to_lon_grad(length, end_lat) * np.cos(angle)
    end_position = {'lat': end_lat, 'lon': end_lon, 'uid': vector[0]['detection_uid'], 'type': 'end'}

    return [start_position, end_position]
