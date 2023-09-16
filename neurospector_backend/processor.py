from .yolo_detector import Detector
from .database import Database
from PIL import Image
from .utils import get_fov_i11
import uuid
from time import sleep


# векторы расходятся от точки геолокации вперед в стороны с максимальным углом отклонения ~33.5 гр
# расстояние между точками геолокации при v=60км/ч и dt=1с - ~17м
# при расчете точек пересечения сначала попробуем брать два вектора, с точки геолокации 1 и точки геолокации 2
# такие, что модуль вектора из точки геолокации не больше ~35м
# желательно вывести зависимость, при которой расстояние между точками геолокации ограничивает длину вектора


def process_images():
    detector = Detector("best.pt", device='cpu')
    while True:
        db = Database()
        queue = db.get_unprocessed_photos()
        for photo in queue:
            geolocation = db.get_location(photo['uid'])
            if geolocation is None:
                continue

            detections = detector.detect(photo['file_path'], [0, 1, 2])
            # посчитать угол от центральной вертикальной линии кадра
            # влево - отрицательный, вправо - положительный
            image = Image.open(photo['file_path'])
            image_center = image.width / 2
            for detection in detections:
                print(detection)
                det_center = detection['coords']['x1'] + (detection['coords']['x2'] - detection['coords']['x1']) / 2
                angle = get_fov_i11(image) / image.width * (image_center - det_center)
                detection_uid = uuid.uuid4().hex
                db.add_detection(
                    detection_uid, photo['uid'], angle, detection['coords']['x1'], detection['coords']['x2'],
                    detection['coords']['y1'], detection['coords']['y2'], 1  # TODO: lamp count
                )
                db.add_vector(uuid.uuid4().hex, photo['uid'], detection_uid)
            image.close()
            db.mark_photo_as_done(photo['uid'])

        del db
        sleep(5)


if __name__ == "__main__":
    process_images()
