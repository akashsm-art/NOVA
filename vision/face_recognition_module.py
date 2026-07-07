"""
Face Recognition Module (Phase 4).

Uses OpenCV's built-in Haar cascade for face *detection* and its LBPH
recognizer for face *identification*. This combo is used instead of
dlib/face_recognition because it installs cleanly on Windows via
`pip install opencv-contrib-python` with no CMake/Visual Studio toolchain
needed.

Data stored under NOVA/data/:
  faces/<name>/*.png     - captured training images per registered person
  face_model.yml         - trained LBPH model
  face_labels.json       - maps numeric label -> person name
"""

import json
import os
import time

import cv2
import numpy as np


class FaceAuth:
    def __init__(self, data_dir: str = "data", camera_index: int = 0,
                 confidence_threshold: float = 70.0):
        self.data_dir = data_dir
        self.faces_dir = os.path.join(data_dir, "faces")
        self.model_path = os.path.join(data_dir, "face_model.yml")
        self.labels_path = os.path.join(data_dir, "face_labels.json")
        self.camera_index = camera_index
        # LBPH: LOWER distance = more confident match. Anything above this
        # threshold is treated as "not recognized".
        self.confidence_threshold = confidence_threshold

        os.makedirs(self.faces_dir, exist_ok=True)

        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        self.detector = cv2.CascadeClassifier(cascade_path)
        self.recognizer = cv2.face.LBPHFaceRecognizer_create()
        self.labels = self._load_labels()
        self.camera = None

        if os.path.exists(self.model_path):
            self.recognizer.read(self.model_path)

    # ---------- camera control ----------

    def start_camera_stream(self):
        self.camera = cv2.VideoCapture(self.camera_index)
        return self.camera.isOpened()

    def stop_camera_stream(self):
        if self.camera is not None:
            self.camera.release()
            self.camera = None

    def capture_camera_frame(self):
        if self.camera is None:
            return None
        ok, frame = self.camera.read()
        return frame if ok else None

    # ---------- detection ----------

    def detect_face(self, frame):
        """Returns a list of (x, y, w, h) rectangles for faces found in frame."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.detector.detectMultiScale(
            gray, scaleFactor=1.2, minNeighbors=5, minSize=(80, 80)
        )
        return faces, gray

    # ---------- enrollment ----------

    def register_new_face(self, name: str, num_samples: int = 20) -> str:
        """
        Opens the camera and captures training images of `name`'s face,
        then retrains the recognizer on all registered people.
        """
        person_dir = os.path.join(self.faces_dir, name)
        os.makedirs(person_dir, exist_ok=True)

        if not self.start_camera_stream():
            return "Couldn't access the camera."

        collected = 0
        existing = len(os.listdir(person_dir))
        try:
            while collected < num_samples:
                frame = self.capture_camera_frame()
                if frame is None:
                    continue
                faces, gray = self.detect_face(frame)
                for (x, y, w, h) in faces:
                    face_crop = gray[y:y + h, x:x + w]
                    face_crop = cv2.resize(face_crop, (200, 200))
                    img_path = os.path.join(
                        person_dir, f"{existing + collected}.png"
                    )
                    cv2.imwrite(img_path, face_crop)
                    collected += 1
                    time.sleep(0.15)  # slight delay so samples vary a bit
                    if collected >= num_samples:
                        break
        finally:
            self.stop_camera_stream()

        if collected == 0:
            return f"I couldn't see a clear face for {name}. Try again with better lighting."

        self._train_model()
        return f"Registered {collected} face samples for {name} and updated the model."

    def _train_model(self):
        images, labels = [], []
        self.labels = {}
        next_label = 0

        for name in sorted(os.listdir(self.faces_dir)):
            person_dir = os.path.join(self.faces_dir, name)
            if not os.path.isdir(person_dir):
                continue
            self.labels[str(next_label)] = name
            for fname in os.listdir(person_dir):
                img = cv2.imread(os.path.join(person_dir, fname), cv2.IMREAD_GRAYSCALE)
                if img is None:
                    continue
                images.append(img)
                labels.append(next_label)
            next_label += 1

        if not images:
            return

        self.recognizer.train(images, np.array(labels))
        self.recognizer.save(self.model_path)
        self._save_labels()

    def _load_labels(self) -> dict:
        if os.path.exists(self.labels_path):
            with open(self.labels_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _save_labels(self):
        with open(self.labels_path, "w", encoding="utf-8") as f:
            json.dump(self.labels, f, indent=2)

    # ---------- identification ----------

    def identify_known_user(self, frame):
        """Returns (name, confidence) for the best-matching face, or (None, None)."""
        if not self.labels:
            return None, None

        faces, gray = self.detect_face(frame)
        if len(faces) == 0:
            return None, None

        # Use the largest detected face (closest to camera)
        x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
        face_crop = cv2.resize(gray[y:y + h, x:x + w], (200, 200))

        label_id, distance = self.recognizer.predict(face_crop)
        if distance <= self.confidence_threshold:
            return self.labels.get(str(label_id)), distance
        return "unknown", distance

    def verify_owner(self, owner_name: str, timeout_seconds: int = 8) -> bool:
        """
        Opens the camera for up to `timeout_seconds` trying to positively
        identify `owner_name`. Returns True as soon as a confident match
        is found, False if the timeout elapses or an unknown/other person
        is all that's seen.
        """
        if not self.start_camera_stream():
            return False

        start = time.time()
        try:
            while time.time() - start < timeout_seconds:
                frame = self.capture_camera_frame()
                if frame is None:
                    continue
                name, _confidence = self.identify_known_user(frame)
                if name == owner_name:
                    return True
        finally:
            self.stop_camera_stream()

        return False
