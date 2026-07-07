"""
System Automation Module.
Lets Nova open/close applications, search for files, and run scripts
on Windows.
"""

import os
import subprocess
import fnmatch

import psutil


class SystemControl:
    def __init__(self, app_aliases: dict):
        # e.g. {"chrome": "chrome.exe", "notepad": "notepad.exe"}
        self.app_aliases = {k.lower(): v for k, v in app_aliases.items()}

    def resolve_app(self, spoken_name: str) -> str:
        """Map a spoken app name (e.g. 'chrome') to its executable/command."""
        spoken_name = spoken_name.strip().lower()
        return self.app_aliases.get(spoken_name, spoken_name)

    def open_application(self, spoken_name: str) -> str:
        """Opens an installed application. Returns a status message."""
        target = self.resolve_app(spoken_name)
        try:
            os.startfile(target)  # noqa: S606 (Windows-only, by design)
            return f"Opening {spoken_name}"
        except FileNotFoundError:
            try:
                subprocess.Popen(target, shell=True)
                return f"Opening {spoken_name}"
            except Exception:
                return f"I couldn't find an app called {spoken_name}"
        except Exception as e:
            return f"I couldn't open {spoken_name}: {e}"

    def close_application(self, spoken_name: str) -> str:
        """Closes a running application by matching its process name."""
        target = self.resolve_app(spoken_name).lower().replace(".exe", "")
        closed_any = False

        for proc in psutil.process_iter(["pid", "name"]):
            name = (proc.info.get("name") or "").lower().replace(".exe", "")
            if target in name:
                try:
                    proc.terminate()
                    closed_any = True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

        if closed_any:
            return f"Closed {spoken_name}"
        return f"{spoken_name} doesn't seem to be running"

    def search_files(self, file_name: str, search_root: str = None) -> list:
        """Searches for files matching file_name under search_root (default: user home)."""
        search_root = search_root or os.path.expanduser("~")
        matches = []
        pattern = f"*{file_name}*"

        for root, _dirs, files in os.walk(search_root):
            for f in fnmatch.filter(files, pattern):
                matches.append(os.path.join(root, f))
            if len(matches) >= 20:
                break

        return matches

    def run_script(self, script_path: str) -> str:
        """Executes a script (.py, .bat, .ps1) and returns a status message."""
        if not os.path.exists(script_path):
            return f"Script not found: {script_path}"

        try:
            if script_path.endswith(".py"):
                subprocess.Popen(["python", script_path], shell=True)
            elif script_path.endswith(".ps1"):
                subprocess.Popen(
                    ["powershell", "-ExecutionPolicy", "Bypass", "-File", script_path]
                )
            else:
                subprocess.Popen(script_path, shell=True)
            return f"Running {script_path}"
        except Exception as e:
            return f"Couldn't run {script_path}: {e}"

    def shutdown_computer(self, delay_seconds: int = 5) -> str:
        subprocess.Popen(["shutdown", "/s", "/t", str(delay_seconds)], shell=True)
        return f"Shutting down in {delay_seconds} seconds"

    def restart_computer(self, delay_seconds: int = 5) -> str:
        subprocess.Popen(["shutdown", "/r", "/t", str(delay_seconds)], shell=True)
        return f"Restarting in {delay_seconds} seconds"

    def lock_system(self) -> str:
        subprocess.Popen("rundll32.exe user32.dll,LockWorkStation", shell=True)
        return "Locking the system"
