import base64
import io
import json
import tempfile
import time
import unittest
from pathlib import Path

from PIL import Image
from qwen_observation import (load_robot_context, unknown_robot_context, prepare_observation,
                              make_payload, validate_response)


class ObservationTests(unittest.TestCase):
    def make_observation(self, size=(1280, 720), objects=None):
        image = Image.new('RGB', size, 'navy')
        output = io.BytesIO()
        image.save(output, format='JPEG')
        return prepare_observation(output.getvalue(), objects or [], (100, 20),
                                   time.monotonic(), 'test-detector', 'Observe the chair',
                                   unknown_robot_context())

    def test_matching_image_boxes_and_clean_pixels(self):
        jpeg, observation = self.make_observation(objects=[
            {'label': 'chair', 'confidence': .8, 'box': [640, 360, 1280, 720]}])
        payload = make_payload(jpeg, 'test', observation)
        image = Image.open(io.BytesIO(base64.b64decode(payload['messages'][1]['images'][0])))
        evidence = json.loads(payload['messages'][1]['content'])
        self.assertEqual(image.size, (768, 432))
        self.assertEqual(evidence['frame']['attached_image_size'], list(image.size))
        self.assertEqual(evidence['perception']['detections'][0]['box_xyxy_pixels'], [384, 216, 768, 432])
        self.assertFalse(evidence['frame']['annotations_drawn'])
        # A box edge must still be the source image color, not a drawn green line.
        self.assertLess(image.getpixel((384, 216))[1], 10)

    def test_portrait_coordinates(self):
        _, obs = self.make_observation(size=(600, 1200), objects=[
            {'label': 'person', 'confidence': .9, 'box': [0, 600, 600, 1200]}])
        self.assertEqual(obs['frame']['attached_image_size'], [384, 768])
        self.assertEqual(obs['perception']['detections'][0]['box_xyxy_pixels'], [0, 384, 384, 768])

    def test_unknown_geometry_is_explicit(self):
        _, obs = self.make_observation(objects=[{'label': 'chair', 'confidence': .8, 'box': [0, 0, 20, 20]}])
        self.assertIsNone(obs['perception']['detections'][0]['range_m'])
        self.assertIsNone(obs['robot']['pose'])
        self.assertIsNone(obs['robot']['lidar'])
        self.assertEqual(obs['frame']['timestamp_basis'], 'pc_packet_receive')
        self.assertIsNone(obs['frame']['capture_age_seconds'])

    def test_object_ids_are_observation_scoped(self):
        obj = [{'label': 'chair', 'confidence': .8, 'box': [0, 0, 20, 20]}]
        _, first = self.make_observation(objects=obj)
        _, second = self.make_observation(objects=obj)
        ref = first['perception']['detections'][0]['object_id']
        response = {'summary': 'chair', 'relevant_object_ids': [ref], 'uncertainties': []}
        self.assertEqual(validate_response(response, first), response)
        with self.assertRaises(ValueError):
            validate_response(response, second)

    def test_unknown_ids_and_motion_fields_are_rejected(self):
        _, obs = self.make_observation()
        with self.assertRaises(ValueError):
            validate_response({'summary': 'x', 'relevant_object_ids': ['invented'], 'uncertainties': []}, obs)
        with self.assertRaises(ValueError):
            validate_response({'summary': 'x', 'relevant_object_ids': [], 'uncertainties': [], 'cmd_vel': 1}, obs)

    def test_empty_detection_list(self):
        _, obs = self.make_observation()
        response = {'summary': 'unknown scene', 'relevant_object_ids': [], 'uncertainties': ['No detections']}
        self.assertEqual(validate_response(response, obs), response)

    def test_context_freshness_and_motion_authority(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'context.json'
            path.write_text(json.dumps({'updated_at_unix_s': 100, 'pose': {'frame_id': 'map'},
                                       'motion_execution_enabled': True}))
            current = load_robot_context(path, now=102)
            self.assertEqual(current['status'], 'available')
            self.assertFalse(current['motion_execution_enabled'])
            self.assertIsNone(current['lidar'])
            self.assertEqual(load_robot_context(path, now=106)['status'], 'unavailable')
            self.assertEqual(load_robot_context(path, now=99)['status'], 'unavailable')
            path.write_text('{bad json')
            self.assertEqual(load_robot_context(path, now=102)['status'], 'unavailable')


if __name__ == '__main__':
    unittest.main()
