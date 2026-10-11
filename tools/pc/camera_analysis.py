"""Receive Pi video, run local Ollama vision, and publish PC Foxglove images."""
import argparse
import io
import json
import logging
import threading
import time
import urllib.request
from pathlib import Path

import foxglove
import av
from foxglove.messages import CompressedImage, CompressedVideo, Timestamp
from PIL import Image, ImageDraw, ImageFont
from object_detection import ObjectDetector
from qwen_observation import prepare_observation, make_payload, validate_response, load_robot_context

LOG = logging.getLogger("camera_analysis")


def publish(topic, jpeg, stamp):
    foxglove.log(topic, CompressedImage(timestamp=Timestamp(*stamp),
                 frame_id="camera", data=jpeg, format="jpeg"))


def receive(url, latest, lock, stop):
    while not stop.is_set():
        try:
            with av.open(url, format="mpegts", options={"fflags": "nobuffer", "flags": "low_delay",
                         "probesize": "32768", "analyzeduration": "0"}, timeout=(10, 5)) as video:
                stream = video.streams.video[0]
                have_keyframe = False
                count, byte_count, started = 0, 0, time.monotonic()
                for packet in video.demux(stream):
                    if stop.is_set():
                        return
                    if not packet.size:
                        continue
                    if not have_keyframe:
                        if not packet.is_keyframe:
                            continue
                        have_keyframe = True
                    # MPEG-TS demux provides one Annex-B H.264 access unit per packet.
                    # Encoding disables B-frames and repeats SPS/PPS at each IDR.
                    now_ns = time.time_ns()
                    stamp = (now_ns // 1_000_000_000, now_ns % 1_000_000_000)
                    foxglove.log("/pc/camera/live", CompressedVideo(timestamp=Timestamp(*stamp),
                                 frame_id="camera", data=bytes(packet), format="h264"))
                    byte_count += packet.size
                    for frame in packet.decode():
                        with lock:
                            latest[:] = [(frame.to_image(), stamp, time.monotonic())]
                        count += 1
                    elapsed = time.monotonic() - started
                    if elapsed >= 10:
                        LOG.info("H.264 decoded %.1f fps, %.2f Mbps", count / elapsed,
                                 byte_count * 8 / elapsed / 1e6)
                        count, byte_count, started = 0, 0, time.monotonic()
        except Exception:
            if not stop.is_set():
                LOG.exception("Video disconnected; retrying")
                stop.wait(3)


def analyze(image, model, observation):
    body = json.dumps(make_payload(image, model, observation), allow_nan=False).encode()
    request = urllib.request.Request("http://127.0.0.1:11434/api/chat", body,
                                     {"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=180) as response:
        result = json.load(response)
    return validate_response(json.loads(result["message"]["content"]), observation)


def overlay(jpeg, result, latency, model):
    image = Image.open(io.BytesIO(jpeg)).convert("RGB")
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 22)
    text = str(result.get("summary", "No summary"))[:240]
    words, lines, line = text.split(), [], ""
    for word in words:
        candidate = (line + " " + word).strip()
        if draw.textlength(candidate, font=font) > image.width - 30:
            lines.append(line)
            line = word
        else:
            line = candidate
    lines.append(line)
    detector_name = result.get('detector', 'detector')
    lines.insert(0, f"Sampled frame | {model} description | {detector_name} boxes | {latency:.1f}s")
    header_height = 12 + 28 * len(lines)
    canvas = Image.new("RGB", (image.width, image.height + header_height), "black")
    canvas.paste(image, (0, header_height))
    draw = ImageDraw.Draw(canvas)
    draw.multiline_text((10, 5), "\n".join(lines), font=font, fill="white", spacing=4)
    if result.get('coordinate_space') != 'original_image_pixels':
        raise ValueError('Detector boxes must use original image pixel coordinates')
    for obj in result.get("objects", []):
        left, top, right, bottom = obj['box']
        coords = (left, top + header_height, right, bottom + header_height)
        draw.rectangle(coords, outline="lime", width=3)
        label = f"{obj['label']} {obj['confidence']:.0%}"
        label_width = draw.textlength(label, font=font)
        label_x = max(0, min(left, image.width - label_width - 8))
        label_y = min(max(header_height, top + header_height - 27), canvas.height - 28)
        draw.rectangle((label_x, label_y, label_x + label_width + 8, label_y + 27), fill="black")
        draw.text((label_x + 4, label_y), label, font=font, fill="lime")
    image = canvas
    output = io.BytesIO()
    image.save(output, format="JPEG", quality=90)
    return output.getvalue()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video-url", default="tcp://127.0.0.1:8554")
    parser.add_argument("--model", default="qwen2.5vl:7b")
    parser.add_argument("--detector", default="runtime/models/yolo11s.pt")
    parser.add_argument("--confidence", type=float, default=0.5)
    parser.add_argument("--task", default="Describe the scene and identify task-relevant objects. Observe only.")
    parser.add_argument("--robot-context-file", type=Path)
    parser.add_argument("--interval", type=float, default=5)
    parser.add_argument("--once", action="store_true", help="Capture and analyze one real frame, then exit")
    parser.add_argument("--video-only", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    output = Path("runtime")
    output.mkdir(exist_ok=True)
    detector = None if args.video_only else ObjectDetector(args.detector, args.confidence)
    server = foxglove.start_server(name="Rover PC video and local vision", host="127.0.0.1", port=8766)
    latest, lock, stop = [], threading.Lock(), threading.Event()
    thread = threading.Thread(target=receive, args=(args.video_url, latest, lock, stop), daemon=True)
    thread.start()
    LOG.info("Foxglove PC endpoint ws://127.0.0.1:8766")
    try:
        deadline = time.monotonic() + 30
        while not latest:
            if time.monotonic() > deadline:
                raise TimeoutError("No camera frame received in 30 seconds")
            time.sleep(.1)
        while True:
            if args.video_only:
                time.sleep(1)
                continue
            with lock:
                image, stamp, received = latest[0]
            if time.monotonic() - received > 3:
                LOG.warning("Waiting for fresh camera data")
                time.sleep(1)
                continue
            started = time.monotonic()
            try:
                buffer = io.BytesIO()
                image.save(buffer, format="JPEG", quality=90)
                jpeg = buffer.getvalue()
                detected_at = time.monotonic()
                objects = detector.detect(image)
                detection_seconds = time.monotonic() - detected_at
                attached_image, observation = prepare_observation(
                    jpeg, objects, stamp, received, Path(args.detector).stem, args.task,
                    load_robot_context(args.robot_context_file))
                (output / 'qwen-frame.jpg').write_bytes(attached_image)
                (output / 'qwen-input.json').write_text(json.dumps(observation, indent=2, allow_nan=False), encoding='utf-8')
                foxglove.log('/pc/vision/observation', observation)
                try:
                    description = analyze(attached_image, args.model, observation)
                except Exception:
                    LOG.exception('Scene description failed; detector boxes remain available')
                    description = {'summary': 'Scene description unavailable', 'relevant_object_ids': [], 'uncertainties': ['Model request or validation failed']}
                result = {**description, 'frame_id': observation['frame']['id'],
                          'task': args.task,
                          'objects': [{**obj, 'object_id': observation['perception']['detections'][index]['object_id']
                                       if index < len(observation['perception']['detections']) else None}
                                      for index, obj in enumerate(objects)],
                          'coordinate_space': 'original_image_pixels',
                          'image_size': [image.width, image.height],
                          'detector': Path(args.detector).stem, 'detection_seconds': detection_seconds,
                          'robot_context_status': observation['robot']['status']}
                latency = time.monotonic() - started
                annotated = overlay(jpeg, result, latency, args.model)
                publish("/pc/camera/analyzed", annotated, stamp)
                foxglove.log("/pc/vision/result", {"model": args.model, "latency_seconds": latency,
                             "source_stamp": {"sec": stamp[0], "nsec": stamp[1]}, **result})
                (output / "camera.jpg").write_bytes(jpeg)
                (output / "analyzed.jpg").write_bytes(annotated)
                (output / "analysis.json").write_text(json.dumps({"model": args.model,
                    "latency_seconds": latency, "source_stamp": stamp, **result}, indent=2), encoding="utf-8")
                LOG.info("Analysis %.1fs: %s", latency, result.get("summary"))
            except Exception:
                LOG.exception("Local analysis failed; live video continues")
                if args.once:
                    raise
            if args.once:
                return
            time.sleep(max(0, args.interval - (time.monotonic() - started)))
    finally:
        stop.set()
        thread.join(timeout=3)
        server.stop()


if __name__ == "__main__":
    main()
