"""
Command Processing Engine.
Rule-based intent detection for Phase 1-3 of the Nova roadmap
(no cloud AI yet -- that's a later phase). Matches spoken text
against simple patterns and dispatches to the right action.
"""

import datetime
import os
import re

from automation.system_control import SystemControl
from core.memory_manager import MemoryManager


EXIT_PHRASES = {"exit", "quit", "stop listening", "shutdown nova", "goodbye nova"}

# Commands that should require a positive face-recognition match (Phase 4)
# before they're allowed to run, when face auth is enabled.
PRIVILEGED_PATTERNS = (
    re.compile(r"lock (the )?(system|computer|pc)"),
    re.compile(r"restart (the )?(computer|pc|system)"),
    re.compile(r"shut ?down (the )?(computer|pc|system)"),
    re.compile(r"close (.+)"),
)


class CommandProcessor:
    def __init__(self, system_control: SystemControl, assistant_name: str = "Nova",
                 memory: MemoryManager = None, face_auth=None):
        self.system_control = system_control
        self.assistant_name = assistant_name
        self.memory = memory
        self.face_auth = face_auth

    def requires_owner_verification(self, text: str) -> bool:
        """Whether this command should be gated behind a face-recognition check."""
        text = text.strip().lower()
        return any(p.search(text) for p in PRIVILEGED_PATTERNS)

    def process_user_command(self, text: str) -> tuple[str, bool]:
        """
        Takes raw recognized text, figures out intent, executes it,
        and returns (response_text, should_exit).
        """
        if not text:
            return "", False

        text = text.strip().lower()

        if any(phrase in text for phrase in EXIT_PHRASES):
            return "Shutting down. Goodbye!", True

        if match := re.search(r"register (my )?face(?: as (.+))?", text):
            name = (match.group(2) or "owner").strip()
            if not self.face_auth:
                return "Face recognition isn't set up.", False
            return self.face_auth.register_new_face(name), False

        if match := re.search(r"remember (?:that )?my (.+?) is (.+)", text):
            key = match.group(1).strip().replace(" ", "_")
            value = match.group(2).strip()
            if self.memory:
                self.memory.store_memory(key, value, source="user")
                return f"Got it, I'll remember your {match.group(1).strip()} is {value}.", False
            return "I don't have memory set up yet.", False

        if match := re.search(r"what (?:is|was) my (.+)", text):
            key = match.group(1).strip().rstrip("?").replace(" ", "_")
            if self.memory:
                value = self.memory.retrieve_memory(key)
                if value:
                    return f"Your {match.group(1).strip().rstrip('?')} is {value}.", False
                return f"I don't have anything remembered for {match.group(1).strip().rstrip('?')}.", False
            return "I don't have memory set up yet.", False

        if "what do you remember" in text or "list what you know" in text:
            if self.memory:
                memories = self.memory.list_all_memories()
                if not memories:
                    return "I don't have anything stored about you yet.", False
                items = ", ".join(f"{m['key'].replace('_', ' ')}: {m['value']}" for m in memories[:5])
                return f"Here's what I remember: {items}.", False
            return "I don't have memory set up yet.", False

        if match := re.search(r"open (.+)", text):
            app = match.group(1).strip()
            return self.system_control.open_application(app), False

        if match := re.search(r"close (.+)", text):
            app = match.group(1).strip()
            return self.system_control.close_application(app), False

        if match := re.search(r"find file (.+)|search for file (.+)", text):
            name = (match.group(1) or match.group(2)).strip()
            results = self.system_control.search_files(name)
            if not results:
                return f"I couldn't find any file matching {name}", False
            preview = ", ".join(os.path.basename(p) for p in results[:5])
            return f"I found {len(results)} matches. Top results: {preview}", False

        if "what time is it" in text or "current time" in text:
            now = datetime.datetime.now().strftime("%I:%M %p")
            return f"It's {now}", False

        if "what's the date" in text or "today's date" in text or "what day is it" in text:
            today = datetime.datetime.now().strftime("%A, %B %d, %Y")
            return f"Today is {today}", False

        if "lock" in text and ("system" in text or "computer" in text or "pc" in text):
            return self.system_control.lock_system(), False

        if "restart" in text and ("computer" in text or "pc" in text or "system" in text):
            return self.system_control.restart_computer(), False

        if "shut down" in text or "shutdown" in text:
            if "computer" in text or "pc" in text or "system" in text:
                return self.system_control.shutdown_computer(), False

        if "hello" in text or "hi nova" in text or "hey nova" in text:
            return f"Hello! I'm {self.assistant_name}, how can I help you?", False

        if "who are you" in text or "what are you" in text:
            return (
                f"I'm {self.assistant_name}, your personal AI assistant. "
                "I can open apps, find files, and answer simple questions."
            ), False

        return "I didn't quite catch a command I know how to run yet. Could you rephrase that?", False
