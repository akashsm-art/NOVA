"""
Emotion Detection Module (Phase 5) — real model version.

Facial emotion is now detected with a real pretrained deep-learning
model: Microsoft's FER+ CNN (Barsoum et al., trained on crowd-sourced
relabeled FER2013 images), distributed as ONNX and run locally through
onnxruntime (CPU, no GPU needed, no TensorFlow/PyTorch install).

Output classes: neutral, happiness, surprise, sadness, anger, disgust,
fear, contempt — each with a confidence score.

Voice tone still uses a lightweight loudness (RMS) heuristic — there's
no similarly small, dependency-light pretrained *voice* emotion model;
real ones (e.g. wav2vec2-based) need PyTorch and a much larger download.
Let me know if you want that added too.
"""

import audioop

import cv2
import numpy as np
import onnxruntime as ort

from emotion.download_model import ensure_model_downloaded

FER_LABELS = ["neutral", "happiness", "surprise", "sadness", "anger", "disgust", "fear", "contempt"]


def _softmax(x: np.ndarray) -> np.ndarray:
    e = np.exp(x - np.max(x))
    return e / e.sum()


class EmotionDetector:
    def __init__(self, camera_index: int = 0, model_path: str = "data/emotion-ferplus-8.onnx"):
        self.camera_index = camera_index

        haar = cv2.data.haarcascades
        self.face_cascade = cv2.CascadeClassifier(haar + "haarcascade_frontalface_default.xml")

        model_path = ensure_model_downloaded(model_path)
        self.session = ort.InferenceSession(model_path, providers=["CPUExecutionProvider"])
        self.input_name = self.session.get_inputs()[0].name

    # ---------- camera ----------

    def capture_snapshot(self):
        """Grabs a single frame from the webcam (with brief warmup)."""
        cam = cv2.VideoCapture(self.camera_index)
        if not cam.isOpened():
            return None

        frame = None
        try:
            for _ in range(5):
                ok, f = cam.read()
                if ok:
                    frame = f
        finally:
            cam.release()

        return frame

    # ---------- facial ----------

    def _detect_largest_face(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5, minSize=(80, 80))
        if len(faces) == 0:
            return None
        x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
        return gray[y:y + h, x:x + w]

    def analyze_facial_expression(self, frame) -> dict:
        """
        Runs the real FER+ model on the largest detected face.
        Returns {"emotion": <label or "no_face">, "confidence": float, "scores": {label: prob}}
        """
        if frame is None:
            return {"emotion": "no_face", "confidence": 0.0, "scores": {}}

        face = self._detect_largest_face(frame)
        if face is None:
            return {"emotion": "no_face", "confidence": 0.0, "scores": {}}

        face_resized = cv2.resize(face, (64, 64)).astype(np.float32)
        input_tensor = face_resized.reshape(1, 1, 64, 64)

        raw_scores = self.session.run(None, {self.input_name: input_tensor})[0][0]
        probs = _softmax(raw_scores)

        best_idx = int(np.argmax(probs))
        scores = {label: float(p) for label, p in zip(FER_LABELS, probs)}

        return {
            "emotion": FER_LABELS[best_idx],
            "confidence": float(probs[best_idx]),
            "scores": scores,
        }

    # ---------- voice (heuristic) ----------

    def analyze_voice_tone(self, audio) -> str:
        """
        Takes a speech_recognition AudioData object and returns a rough
        loudness-based tone label: 'flat', 'calm', or 'energetic'.
        Returns 'unknown' if no audio was provided.
        """
        if audio is None:
            return "unknown"

        raw = audio.get_raw_data()
        rms = audioop.rms(raw, audio.sample_width)

        if rms < 300:
            return "flat"
        if rms < 3000:
            return "calm"
        return "energetic"

    # ---------- combined ----------

    def detect_emotion_state(self, audio=None) -> dict:
        """
        Takes a snapshot + (optionally) the last utterance's audio, and
        returns a combined reading.
        """
        frame = self.capture_snapshot()
        facial_result = self.analyze_facial_expression(frame)
        voice_state = self.analyze_voice_tone(audio)

        label, intensity = self._combine(facial_result, voice_state)
        return {
            "facial": facial_result["emotion"],
            "facial_confidence": facial_result["confidence"],
            "facial_scores": facial_result["scores"],
            "voice": voice_state,
            "label": label,
            "intensity": intensity,
        }

    def _combine(self, facial_result: dict, voice_state: str) -> tuple:
        facial_emotion = facial_result["emotion"]
        confidence = facial_result["confidence"]

        # Low-confidence face reads are unreliable — don't overclaim.
        if facial_emotion == "no_face" or confidence < 0.35:
            if voice_state == "flat":
                return "tired", 40
            return "uncertain", 20

        intensity = int(confidence * 100)

        if facial_emotion in ("sadness", "fear") or voice_state == "flat":
            return "low_mood_or_tired", max(intensity, 50)
        if facial_emotion in ("anger", "disgust") or voice_state == "energetic":
            return "stressed_or_frustrated", max(intensity, 50)
        if facial_emotion in ("happiness", "surprise"):
            return "happy", intensity
        return "neutral", intensity

    def suggest_relaxation_action(self, label: str) -> str:
        suggestions = {
            "low_mood_or_tired": "You seem a little tired or down. Maybe take a short break or grab some water?",
            "stressed_or_frustrated": "You sound a bit stressed or frustrated. Want to take a quick breather?",
            "happy": "You seem to be in a good mood!",
            "neutral": "You seem okay. Let me know if you'd like a break.",
            "uncertain": "I couldn't get a clear read this time — try again with better lighting or facing the camera.",
        }
        return suggestions.get(label, "I'm not fully sure how you're doing, but I'm here if you need anything.")
