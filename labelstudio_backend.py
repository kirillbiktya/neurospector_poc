import random
import label_studio_sdk
from label_studio_ml.model import LabelStudioMLBase
from label_studio_ml.utils import is_skipped, get_image_size
import torch
from numpy import random
from models.experimental import attempt_load
from utils.datasets import LoadStreams, LoadImages
from utils.general import check_img_size, check_requirements, check_imshow, non_max_suppression, apply_classifier, \
    scale_coords, xyxy2xywh, strip_optimizer, set_logging, increment_path
from utils.torch_utils import select_device, load_classifier, time_synchronized, TracedModel

LABEL_STUDIO_HOST = 'http://192.168.1.2:8080'
LABEL_STUDIO_API_KEY = 'api-key'

LABELS = ['labels list here']
CLASSES = [2, 3]
MODEL_PATH = "best.pt"
LOCAL_DATASET_PATH = "/home/kirill/.local/share/label-studio/media/upload/6/"


class Detector:
    def __init__(
            self,
            weights,
            device="0",
            imgsz=640,
            augment=False,
            conf_thres=0.25,
            iou_thres=0.45,
            agnostic_nms=False
    ):
        self.weights = weights
        self.source = None
        self.classes = None
        self.device = select_device(device)
        self.imgsz = imgsz
        self.augment = augment
        self.conf_thres = conf_thres
        self.iou_thres = iou_thres
        self.agnostic_nms = agnostic_nms

        self.old_img_b = None
        self.old_img_h = None
        self.old_img_w = None

        self._prepare_net()

    def __del__(self):
        return

    def _prepare_net(self):
        self.half = self.device.type != 'cpu'
        self.model = attempt_load(self.weights, map_location=self.device)
        self.stride = int(self.model.stride.max())
        self.imgsz = check_img_size(self.imgsz, s=self.stride)
        self.model = TracedModel(self.model, self.device, self.imgsz)
        if self.half:
            self.model.half()
        self.names = self.model.module.names if hasattr(self.model, 'module') else self.model.names
        self.colors = [[random.randint(0, 255) for _ in range(3)] for _ in self.names]

        if self.device.type != 'cpu':
            self.model(torch.zeros(1, 3, self.imgsz, self.imgsz).to(self.device).type_as(next(self.model.parameters())))
        self.old_img_w = self.old_img_h = self.imgsz
        self.old_img_b = 1

    def detect(self, source, classes, task=None):
        dataset = LoadImages(source, img_size=self.imgsz, stride=self.stride)

        results = []
        for path, img, im0s, vid_cap in dataset:
            img = torch.from_numpy(img).to(self.device)
            img = img.half() if self.half else img.float()  # uint8 to fp16/32
            img /= 255.0  # 0 - 255 to 0.0 - 1.0
            if img.ndimension() == 3:
                img = img.unsqueeze(0)

            # Warmup
            if self.device.type != 'cpu' and (
                    self.old_img_b != img.shape[0] or self.old_img_h != img.shape[2] or self.old_img_w != img.shape[3]):
                self.old_img_b = img.shape[0]
                self.old_img_h = img.shape[2]
                self.old_img_w = img.shape[3]
                for i in range(3):
                    self.model(img, augment=self.augment)[0]

            # Inference
            with torch.no_grad():  # Calculating gradients would cause a GPU memory leak
                pred = self.model(img, augment=self.augment)[0]

            # Apply NMS
            pred = non_max_suppression(pred, self.conf_thres, self.iou_thres, classes=classes, agnostic=self.agnostic_nms)

            # Process detections
            for i, det in enumerate(pred):  # detections per image
                p, s, im0, frame = path, '', im0s, getattr(dataset, 'frame', 0)
                gn = torch.tensor(im0.shape)[[1, 0, 1, 0]]  # normalization gain whwh
                if len(det):
                    # Rescale boxes from img_size to im0 size
                    det[:, :4] = scale_coords(img.shape[2:], det[:, :4], im0.shape).round()

                    # Write results
                    for *xyxy, conf, cls in reversed(det):
                        if task is None:
                            xywh = (xyxy2xywh(torch.tensor(xyxy).view(1, 4)) / gn).view(-1).tolist()  # normalized xywh
                            print(cls, conf, *xywh)
                            return
                        else:
                            results.append(
                                {
                                    'confidence': float(conf.item()), 'class': int(cls.item()), 'coords': {
                                        'x': float(xyxy[0]),'y': float(xyxy[1]),'w': float(xyxy[2]),'h': float(xyxy[3])
                                    }
                                }
                            )
        return results


detector = Detector(MODEL_PATH)


class YOLOv7(LabelStudioMLBase):
    def _get_image_path(self, task):
        image_url = task['data']['image']
        im_name = image_url.split('/')[-1]
        return LOCAL_DATASET_PATH + im_name

    def predict(self, tasks, **kwargs):
        """ This is where inference happens:
            model returns the list of predictions based on input list of tasks

            :param tasks: Label Studio tasks in JSON format
        """
        results = []
        scores = []

        for task in tasks:
            # if is_skipped(task):
            #     continue
            image_path = self._get_image_path(task)
            res = detector.detect(image_path, CLASSES, task)
            img_width, img_height = get_image_size(image_path)
            for r in res:
                results.append({
                    'from_name': 'label',
                    'to_name': 'image',
                    "original_width": img_width,
                    "original_height": img_height,
                    'type': 'rectanglelabels',
                    'value': {
                        'rectanglelabels': [LABELS[r['class']]],
                        'x': r['coords']['x'] / img_width * 100,
                        'y': r['coords']['y'] / img_height * 100,
                        'width': (r['coords']['w'] - r['coords']['x']) / img_width * 100,
                        'height': (r['coords']['h'] - r['coords']['y']) / img_height * 100
                    },
                    'score': r['confidence']
                })
                scores.append(r['confidence'])
        print(results)
        return [{'result': results, 'score': sum(scores) / max(len(scores), 1)}]

    def download_tasks(self, project):
        """
        Download all labeled tasks from project using the Label Studio SDK.
        Read more about SDK here https://labelstud.io/sdk/
        :param project: project ID
        :return:
        """
        ls = label_studio_sdk.Client(LABEL_STUDIO_HOST, LABEL_STUDIO_API_KEY)
        project = ls.get_project(id=project)
        tasks = project.get_labeled_tasks()
        return tasks

    def fit(self, event, data,  **kwargs):
        pass