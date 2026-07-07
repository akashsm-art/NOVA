"""
Text-to-Speech module.
Uses pyttsx3, which works fully offline and relies on the Windows SAPI5
voices that already ship with Windows, so no extra setup is needed.
"""

import pyttsx3


class TextToSpeech:
    def __init__(self, rate: int = 175, volume: float = 1.0, voice_index: int = 0):
        self.engine = pyttsx3.init()
        self.engine.setProperty("rate", rate)
        self.engine.setProperty("volume", volume)

        voices = self.engine.getProperty("voices")
        if voices:
            index = voice_index if voice_index < len(voices) else 0
            self.engine.setProperty("voice", voices[index].id)

    def speak(self, text: str) -> None:
        """Convert text to speech and play it out loud."""
        if not text:
            return
        print(f"Nova: {text}")
        self.engine.say(text)
        self.engine.runAndWait()

    def list_available_voices(self) -> list:
        """Return the list of installed system voices (name + id)."""
        voices = self.engine.getProperty("voices")
        return [{"index": i, "name": v.name, "id": v.id} for i, v in enumerate(voices)]
