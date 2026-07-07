<<<<<<< HEAD
# NOVA — Personal AI Assistant (Phase 1–3, 4 & 6 Prototype)

This is a real, working starting point for the NOVA project, covering:

- **Phase 1** — Environment setup
- **Phase 2** — Core talking assistant (listen → speech-to-text → respond → text-to-speech)
- **Phase 3** — System automation (open/close apps, find files, lock/restart/shutdown PC)
- **Phase 4** — Face recognition login (own-face detection gating privileged commands)
- **Phase 6** — Memory system (remembers facts + logs conversation history in SQLite)

It does **not** yet include emotion detection, cloud AI, phone integration,
or the other later-phase modules — those need extra services/hardware and
are best added once this is solid.

## Phase 4 — Face recognition login

Uses OpenCV's Haar cascade (detection) + LBPH recognizer (identification)
instead of dlib/`face_recognition`, because it installs cleanly on Windows
with just `pip install opencv-contrib-python` — no CMake or Visual Studio
Build Tools required.

**How it works:**
1. Say **"Nova, register my face as `<your name>`"**. Nova opens the
   webcam, captures ~20 samples of your face, and trains a local model
   (stored under `data/faces/`, `data/face_model.yml`).
2. In `config/nova_config.json`, set:
   ```json
   "face_auth_enabled": true,
   "owner_name": "<your name>"
   ```
3. From then on, privileged commands — **lock/restart/shutdown the
   computer** and **close an app** — first open the camera and check that
   the person speaking is actually you before running. If it can't
   confirm you within ~8 seconds, it refuses.

This is a **local convenience check**, not hardened security — it's meant
to stop casual/accidental use of power commands by someone else in the
room, not to resist a determined attacker.

## Phase 6 — Memory system

A local SQLite database at `data/nova_system.db` with two tables:
`user_memory` (facts) and `conversation_history` (every turn you and Nova
exchange). Try:

- "Nova, remember that my project name is Quantum"
- "Nova, what is my project name?"
- "Nova, what do you remember?"

Every command you give and every response Nova gives is also logged to
`conversation_history` automatically, so later phases (like a cloud LLM)
can pull in real context.

## 1. Install prerequisites (Windows)

1. Install **Python 3.10+** from python.org (check "Add to PATH" during install).
2. Open **Command Prompt** in this folder and create a virtual environment:
   ```
   python -m venv venv
   venv\Scripts\activate
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

   **Note on PyAudio (microphone access):** `pip install pyaudio` sometimes
   fails to build on Windows. If it does, install a prebuilt wheel instead:
   ```
   pip install pipwin
   pipwin install pyaudio
   ```

4. Make sure your microphone is enabled in **Windows Settings → Privacy →
   Microphone**, and that Command Prompt/Python is allowed to access it.

## 2. Run Nova

```
python main.py
```

Nova will greet you out loud, then continuously listen. Try saying things like:

- "Open Chrome"
- "Open Notepad"
- "Close Notepad"
- "Find file resume"
- "What time is it"
- "Lock the computer"
- "Exit" (to stop Nova)

## 3. Project structure

```
NOVA/
├── main.py                     # entry point
├── requirements.txt
├── config/
│   └── nova_config.json        # assistant name, voice settings, app aliases, face/memory config
├── core/
│   ├── nova_core.py            # central controller / main loop
│   ├── command_processor.py    # rule-based intent detection & dispatch
│   └── memory_manager.py       # SQLite facts + conversation history (Phase 6)
├── voice/
│   ├── speech_listener.py      # mic → text (SpeechRecognition + Google Web Speech API)
│   └── text_to_speech.py       # text → speech (pyttsx3, fully offline)
├── vision/
│   └── face_recognition_module.py  # OpenCV face detection/recognition (Phase 4)
├── automation/
│   └── system_control.py       # open/close apps, search files, run scripts, power controls
└── data/                       # created at runtime: face_model.yml, nova_system.db, etc.
```

## 4. Adding your own apps

Edit `config/nova_config.json` and add entries to `app_aliases`, e.g.:

```json
"discord": "Discord.exe",
"steam": "steam.exe"
```

The key is what you'll say ("open discord"), the value is the executable
Windows should launch.

## 5. Notes on how recognition works

- Speech-to-text uses Google's free Web Speech API through the
  `speech_recognition` library, which **requires internet access**. There's
  no API key needed for light personal use, but it's a shared free service,
  not something to build a product on.
- Text-to-speech uses `pyttsx3`, which is fully offline and uses the voices
  already installed on Windows (via SAPI5).
- Command understanding right now is rule-based (regex/keyword matching),
  matching your roadmap's Phase 3. Swapping this out for real NLP or a
  cloud LLM (Phase 10 in your roadmap) is a natural next step once this is
  working reliably.

## 6. Suggested next steps (in roadmap order)

1. **Phase 5 — Emotion detection**: analyze tone/expression to trigger
   break suggestions.
2. **Phase 7 — Security/firewall**: expand `security_events` logging and
   add intrusion alerts on repeated failed face verifications.
3. **Phase 10 — Cloud AI**: replace the rule-based `CommandProcessor` with
   a call to an LLM API for open-ended questions it doesn't have a rule for
   (the `conversation_history` table already gives it context to work with).

Each of these can be built the same way this prototype was — as a self-
contained module that plugs into `NovaCore` — so you don't have to rewrite
what's already working.
=======
# NOVA
NOVA: A Hybrid Intelligent Personal AI Assistant with Autonomous Learning, Security, and Multimodal Interaction
>>>>>>> 5376acd9f2ecb7436712ee1f5f013eed26fcbc5b
