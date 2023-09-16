import random
import torch
from numpy import random
from models.experimental import attempt_load
from utils.datasets import LoadImages
from utils.general import check_img_size, non_max_suppression, scale_coords
from utils.torch_utils import select_device, TracedModel


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

    def detect(self, source, classes):
        dataset = LoadImages(source, img_size=self.imgsz, stride=self.stride)

        results = []
        for path, img, im0s, vid_cap in dataset:
            img = torch.from_numpy(img).to(self.device)
            img = img.half() if self.half else img.float()
            img /= 255.0
            if img.ndimension() == 3:
                img = img.unsqueeze(0)
            if self.device.type != 'cpu' and (
                    self.old_img_b != img.shape[0] or self.old_img_h != img.shape[2] or self.old_img_w != img.shape[3]):
                self.old_img_b = img.shape[0]
                self.old_img_h = img.shape[2]
                self.old_img_w = img.shape[3]
                for i in range(3):
                    self.model(img, augment=self.augment)[0]
            with torch.no_grad():
                pred = self.model(img, augment=self.augment)[0]
            pred = non_max_suppression(
                pred, self.conf_thres, self.iou_thres, classes=classes, agnostic=self.agnostic_nms
            )
            for i, det in enumerate(pred):
                p, s, im0, frame = path, '', im0s, getattr(dataset, 'frame', 0)
                # gn = torch.tensor(im0.shape)[[1, 0, 1, 0]]
                if len(det):
                    det[:, :4] = scale_coords(img.shape[2:], det[:, :4], im0.shape).round()
                    for *xyxy, conf, cls in reversed(det):
                        results.append(
                                {
                                    'confidence': float(conf.item()), 'class': int(cls.item()), 'coords': {
                                        'x1': float(xyxy[0]), 'y1': float(xyxy[1]),
                                        'x2': float(xyxy[2]), 'y2': float(xyxy[3])
                                    }
                                }
                        )
        return results
