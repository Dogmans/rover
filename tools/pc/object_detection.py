"""Boxes in original image pixels from a dedicated local object detector."""
import math
import os
from pathlib import Path

os.environ.setdefault('YOLO_CONFIG_DIR', str(Path('runtime/ultralytics').resolve()))
Path(os.environ['YOLO_CONFIG_DIR'], 'Ultralytics').mkdir(parents=True, exist_ok=True)
os.environ.setdefault('YOLO_AUTOINSTALL', 'false')


class ObjectDetector:
    def __init__(self, weights, confidence=0.5):
        if not 0 < confidence <= 1:
            raise ValueError('Detection confidence must be between 0 and 1')
        if not Path(weights).is_file():
            raise FileNotFoundError(f'Download the detector weights first: {weights}')
        from ultralytics import YOLO
        import torch
        torch.set_num_threads(4)
        self.model = YOLO(weights)
        self.confidence = confidence

    def detect(self, image):
        result = self.model.predict(image, imgsz=960, conf=self.confidence,
                                    iou=0.5, max_det=20, device='cpu', verbose=False)[0]
        objects = []
        for box, confidence, category in zip(result.boxes.xyxy.tolist(),
                                             result.boxes.conf.tolist(), result.boxes.cls.tolist()):
            if not all(math.isfinite(v) for v in box):
                continue
            left, top, right, bottom = box
            left, right = max(0, left), min(image.width, right)
            top, bottom = max(0, top), min(image.height, bottom)
            if left >= right or top >= bottom:
                continue
            objects.append({'label': result.names[int(category)], 'confidence': confidence,
                            'box': [left, top, right, bottom]})
        return objects
