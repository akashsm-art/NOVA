"""
Nova Core Controller.
The central orchestrator: loads config, initializes the voice and
automation modules, and runs the main listen -> process -> respond loop.
"""

import json
import os

from voice.speech_listener import SpeechListener
from voice.text_to_speech import TextToSpeech
from automation.system_control import SystemControl
from core.command_processor import CommandProcessor
from core.memory_manager import MemoryManager


class NovaCore:
    def __init__(self, config_path: str = "config/nova_config.json"):
        self.config = self._load_config(config_path)
        self.assistant_name = self.config.get("assistant_name", "Nova")
        self.owner_name = self.config.get("owner_name", "owner")
        self.face_auth_enabled = self.config.get("face_auth_enabled", False)

        self.tts = TextToSpeech(
            rate=self.config.get("voice_rate", 175),
            volume=self.config.get("voice_volume", 1.0),
        )
        self.listener = SpeechListener(
            timeout=self.config.get("listen_timeout_seconds", 6),
            phrase_time_limit=self.config.get("phrase_time_limit_seconds", 8),
        )
        self.system_control = SystemControl(self.config.get("app_aliases", {}))
        self.memory = MemoryManager(db_path=self.config.get("memory_db_path", "data/nova_system.db"))

        self.face_auth = None
        if self.face_auth_enabled:
            # Imported lazily so that people who don't install
            # opencv-contrib-python can still run the voice-only prototype.
            from vision.face_recognition_module import FaceAuth
            self.face_auth = FaceAuth(
                data_dir=self.config.get("face_data_dir", "data"),
                confidence_threshold=self.config.get("face_confidence_threshold", 70.0),
            )

        self.emotion_detector = None
        if self.config.get("emotion_detection_enabled", False):
            from emotion.emotion_detection import EmotionDetector
            self.emotion_detector = EmotionDetector(
                camera_index=self.config.get("camera_index", 0),
                model_path=self.config.get("emotion_model_path", "data/emotion-ferplus-8.onnx"),
            )

        self.command_processor = CommandProcessor(
            self.system_control,
            self.assistant_name,
            memory=self.memory,
            face_auth=self.face_auth,
            emotion_detector=self.emotion_detector,
            speech_listener=self.listener,
        )

    def _load_config(self, config_path: str) -> dict:
        if not os.path.exists(config_path):
            return {}
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def initialize_nova(self) -> None:
        print(f"Initializing {self.assistant_name}...")
        self.tts.speak(f"{self.assistant_name} is online. How can I help you?")

    def run_main_ai_loop(self) -> None:
        """Continuously listens, processes, and responds until told to stop."""
        self.initialize_nova()

        while True:
            text = self.listener.listen_to_user()
            if not text:
                continue

            if (self.face_auth_enabled and self.face_auth
                    and self.command_processor.requires_owner_verification(text)):
                self.tts.speak("Let me confirm it's you first.")
                if not self.face_auth.verify_owner(self.owner_name, timeout_seconds=8):
                    self.tts.speak("I couldn't verify you as the owner, so I won't do that.")
                    continue

            response, should_exit = self.command_processor.process_user_command(text)
            if response:
                self.tts.speak(response)

            self.memory.store_conversation_history(text, response)

            if should_exit:
                break

    def shutdown_nova(self) -> None:
        print(f"{self.assistant_name} has shut down.")
