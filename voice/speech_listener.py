"""
Voice input module.
Listens to the microphone and converts speech to text using Google's
free Web Speech API through the `speech_recognition` library.
(Requires an internet connection for recognition; the mic capture itself
is local.)
"""

import speech_recognition as sr


class SpeechListener:
    def __init__(self, timeout: int = 6, phrase_time_limit: int = 8):
        self.recognizer = sr.Recognizer()
        self.timeout = timeout
        self.phrase_time_limit = phrase_time_limit
        self.microphone = sr.Microphone()

        # One-time ambient noise calibration so recognition is more reliable.
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)

    def listen_to_user(self) -> str:
        """
        Continuously waits for the user to speak, then converts the
        captured audio into text. Returns "" if nothing usable was heard.
        """
        with self.microphone as source:
            print("Listening...")
            try:
                audio = self.recognizer.listen(
                    source,
                    timeout=self.timeout,
                    phrase_time_limit=self.phrase_time_limit,
                )
            except sr.WaitTimeoutError:
                return ""

        return self._speech_to_text(audio)

    def _speech_to_text(self, audio) -> str:
        try:
            text = self.recognizer.recognize_google(audio)
            print(f"You: {text}")
            return text.lower()
        except sr.UnknownValueError:
            return ""
        except sr.RequestError as e:
            print(f"Speech recognition service error: {e}")
            return ""
