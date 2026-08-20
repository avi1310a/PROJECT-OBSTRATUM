import tkinter as tk
from tkinter import scrolledtext, messagebox
import subprocess
import webbrowser
import threading
import os
import re
import ast
import operator
import shutil
import tempfile
import wave
import datetime
import platform
import getpass

import pyttsx3
import speech_recognition as sr
import sounddevice as sd
import numpy as np


# ============================================================
#                       OBSTRATUM
#              Windows AI Desktop Assistant
# ============================================================

NAME = "OBSTRATUM"
VERSION = "2.0"


# ============================================================
#                       USER CONFIG
# ============================================================

# Change ONLY the paths that you actually need.
#
# You can leave applications as "" if OBSTRATUM can find them
# automatically.

CUSTOM_APPS = {

    # ---------------- WINDOWS ----------------

    "edge": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",

    "vscode": r"C:\Users\YOUR_USERNAME\AppData\Local\Programs\Microsoft VS Code\Code.exe",

    "notepad": r"C:\Windows\System32\notepad.exe",

    "calculator": r"C:\Windows\System32\calc.exe",

    "paint": r"C:\Windows\System32\mspaint.exe",

    "cmd": r"C:\Windows\System32\cmd.exe",

    "powershell": r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe",

    # ---------------- GAMES ----------------

    "genshin": r"",

    "ghost of tsushima": r"",

    "minecraft": r"",

    "valorant": r"",

    # ---------------- APPS ----------------

    "steam": r"",

    "discord": r"",

    "spotify": r"",

    "epic games": r"",

}


# ============================================================
#                     WEBSITE DATABASE
# ============================================================

WEBSITES = {

    "youtube":
        "https://www.youtube.com",

    "youtube music":
        "https://music.youtube.com",

    "google":
        "https://www.google.com",

    "github":
        "https://github.com",

    "gmail":
        "https://mail.google.com",

    "google drive":
        "https://drive.google.com",

    "google docs":
        "https://docs.google.com",

    "google classroom":
        "https://classroom.google.com",

    "chatgpt":
        "https://chatgpt.com",

    "wikipedia":
        "https://www.wikipedia.org",

    "reddit":
        "https://www.reddit.com",

    "discord web":
        "https://discord.com/app",

    "spotify web":
        "https://open.spotify.com",

}


# ============================================================
#                    APPLICATION ALIASES
# ============================================================

ALIASES = {

    "microsoft edge": "edge",
    "edge browser": "edge",

    "visual studio code": "vscode",
    "vs code": "vscode",
    "code": "vscode",

    "genshin impact": "genshin",

    "ghost of tsushima director's cut":
        "ghost of tsushima",

    "ghost of tsushima dc":
        "ghost of tsushima",

    "minecraft java":
        "minecraft",

    "riot games":
        "valorant",

    "epic":
        "epic games",

}


# ============================================================
#                    TEXT TO SPEECH
# ============================================================

engine = pyttsx3.init()

engine.setProperty(
    "rate",
    175
)

engine.setProperty(
    "volume",
    1.0
)


def speak(text):

    try:

        engine.say(text)
        engine.runAndWait()

    except Exception:

        pass


# ============================================================
#                     SAFE CALCULATOR
# ============================================================

OPERATORS = {

    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,

    ast.FloorDiv:
        operator.floordiv,

    ast.USub:
        operator.neg,

    ast.UAdd:
        operator.pos,

}


def safe_calculate(expression):

    expression = expression.replace(
        "^",
        "**"
    )

    try:

        tree = ast.parse(
            expression,
            mode="eval"
        )

    except Exception:

        return None

    def evaluate(node):

        if isinstance(
            node,
            ast.Expression
        ):

            return evaluate(
                node.body
            )

        if isinstance(
            node,
            ast.Constant
        ):

            if isinstance(
                node.value,
                (int, float)
            ):

                return node.value

            raise ValueError

        if isinstance(
            node,
            ast.BinOp
        ):

            left = evaluate(
                node.left
            )

            right = evaluate(
                node.right
            )

            operation = OPERATORS.get(
                type(node.op)
            )

            if operation is None:
                raise ValueError

            return operation(
                left,
                right
            )

        if isinstance(
            node,
            ast.UnaryOp
        ):

            value = evaluate(
                node.operand
            )

            operation = OPERATORS.get(
                type(node.op)
            )

            if operation is None:
                raise ValueError

            return operation(
                value
            )

        raise ValueError

    try:

        result = evaluate(tree)

        if (
            isinstance(result, float)
            and result.is_integer()
        ):

            return int(result)

        return result

    except Exception:

        return None


def extract_math(command):

    command = command.lower()

    replacements = {

        "multiplied by": "*",
        "divided by": "/",
        "to the power of": "**",

        "plus": "+",
        "minus": "-",
        "times": "*",
        "divide": "/",
        "power": "**",

    }

    for word, symbol in replacements.items():

        command = command.replace(
            word,
            symbol
        )

    phrases = [

        "calculate",
        "what is",
        "what's",
        "solve",
        "compute",
        "calculate",
        "equals",
        "equal to",

    ]

    for phrase in phrases:

        command = command.replace(
            phrase,
            ""
        )

    expression = re.sub(
        r"[^0-9+\-*/%.() ]",
        "",
        command
    )

    expression = expression.strip()

    if not expression:
        return None

    if not re.search(
        r"\d",
        expression
    ):

        return None

    return expression


# ============================================================
#                  APPLICATION FINDER
# ============================================================

def find_application(name):

    # --------------------------------------------------------
    # Custom configured path
    # --------------------------------------------------------

    custom = CUSTOM_APPS.get(
        name,
        ""
    )

    if custom:

        if os.path.exists(custom):

            return custom

    # --------------------------------------------------------
    # PATH search
    # --------------------------------------------------------

    path = shutil.which(name)

    if path:

        return path

    # --------------------------------------------------------
    # Common Windows locations
    # --------------------------------------------------------

    username = getpass.getuser()

    locations = [

        rf"C:\Users\{username}\AppData\Local\Programs\{name}\{name}.exe",

        rf"C:\Program Files\{name}\{name}.exe",

        rf"C:\Program Files (x86)\{name}\{name}.exe",

    ]

    for path in locations:

        if os.path.exists(path):

            return path

    return None


# ============================================================
#                   LAUNCH APPLICATION
# ============================================================

def launch_application(name):

    path = find_application(
        name
    )

    if not path:

        return (
            f"I couldn't find {name}. "
            f"Add its .exe path in CUSTOM_APPS."
        )

    try:

        subprocess.Popen(
            path
        )

        return (
            f"Launching {name}."
        )

    except Exception as error:

        return (
            f"I couldn't launch {name}: "
            f"{error}"
        )


# ============================================================
#                     WINDOWS TOOLS
# ============================================================

def windows_command(command):

    commands = {

        "file explorer":
            "explorer",

        "explorer":
            "explorer",

        "task manager":
            "taskmgr",

        "control panel":
            "control",

        "settings":
            "start ms-settings:",

        "windows settings":
            "start ms-settings:",

        "terminal":
            "wt",

        "snipping tool":
            "snippingtool",

        "device manager":
            "devmgmt.msc",

        "disk management":
            "diskmgmt.msc",

        "services":
            "services.msc",

    }

    executable = commands.get(
        command
    )

    if not executable:

        return None

    try:

        subprocess.Popen(
            executable,
            shell=True
        )

        return f"Opening {command}."

    except Exception as error:

        return f"Couldn't open {command}: {error}"


# ============================================================
#                     FOLDERS
# ============================================================

def open_folder(folder):

    folders = {

        "desktop":
            os.path.join(
                os.path.expanduser("~"),
                "Desktop"
            ),

        "downloads":
            os.path.join(
                os.path.expanduser("~"),
                "Downloads"
            ),

        "documents":
            os.path.join(
                os.path.expanduser("~"),
                "Documents"
            ),

        "pictures":
            os.path.join(
                os.path.expanduser("~"),
                "Pictures"
            ),

        "videos":
            os.path.join(
                os.path.expanduser("~"),
                "Videos"
            ),

        "music":
            os.path.join(
                os.path.expanduser("~"),
                "Music"
            ),

    }

    path = folders.get(
        folder
    )

    if not path:
        return None

    if not os.path.exists(path):

        return (
            f"I couldn't find your {folder} folder."
        )

    os.startfile(path)

    return (
        f"Opening {folder}."
    )


# ============================================================
#                     WEBSITES
# ============================================================

def open_website(site):

    url = WEBSITES.get(
        site
    )

    if not url:

        return (
            f"I don't know the website {site}."
        )

    webbrowser.open(url)

    return (
        f"Opening {site}."
    )


# ============================================================
#                     SEARCH
# ============================================================

def google_search(query):

    url = (
        "https://www.google.com/search?q="
        + query.replace(
            " ",
            "+"
        )
    )

    webbrowser.open(url)

    return (
        f"Searching Google for {query}."
    )


def youtube_search(query):

    url = (
        "https://www.youtube.com/results?search_query="
        + query.replace(
            " ",
            "+"
        )
    )

    webbrowser.open(url)

    return (
        f"Searching YouTube for {query}."
    )


# ============================================================
#                     SYSTEM INFO
# ============================================================

def system_information():

    computer = platform.node()

    system = platform.system()

    version = platform.version()

    processor = platform.processor()

    return (
        f"Computer: {computer}\n"
        f"Operating system: {system}\n"
        f"Windows version: {version}\n"
        f"Processor: {processor}"
    )


# ============================================================
#                    BASIC AI BRAIN
# ============================================================

def answer_question(command):

    command = command.lower().strip()

    # --------------------------------------------------------
    # Identity
    # --------------------------------------------------------

    if (
        "who are you" in command
        or "what are you" in command
    ):

        return (
            "I am OBSTRATUM, "
            "your Python desktop AI assistant."
        )

    if "your name" in command:

        return (
            "My name is OBSTRATUM."
        )

    if "who made you" in command:

        return (
            "I was created as the "
            "OBSTRATUM Python project."
        )

    # --------------------------------------------------------
    # Greetings
    # --------------------------------------------------------

    if (
        "hello" in command
        or command == "hi"
        or "hey" in command
    ):

        return (
            "Hello. OBSTRATUM is online."
        )

    if "how are you" in command:

        return (
            "All systems are operational."
        )

    # --------------------------------------------------------
    # Capabilities
    # --------------------------------------------------------

    if "what can you do" in command:

        return (
            "I can launch games and applications, "
            "open websites, search Google and YouTube, "
            "perform mathematics, open Windows tools, "
            "control folders, give system information, "
            "and respond to voice commands."
        )

    # --------------------------------------------------------
    # Time
    # --------------------------------------------------------

    if (
        "what time" in command
        or command == "time"
    ):

        current = datetime.datetime.now()

        return (
            "The current time is "
            + current.strftime("%I:%M %p")
        )

    # --------------------------------------------------------
    # Date
    # --------------------------------------------------------

    if (
        "what date" in command
        or "today's date" in command
        or command == "date"
    ):

        current = datetime.datetime.now()

        return (
            "Today is "
            + current.strftime(
                "%d %B %Y"
            )
        )

    # --------------------------------------------------------
    # Python
    # --------------------------------------------------------

    if "what is python" in command:

        return (
            "Python is a high-level programming "
            "language used for software development, "
            "automation, artificial intelligence, "
            "data science, and robotics."
        )

    # --------------------------------------------------------
    # AI
    # --------------------------------------------------------

    if (
        "what is artificial intelligence"
        in command
    ):

        return (
            "Artificial intelligence is the field "
            "of building computer systems that can "
            "perform tasks involving capabilities "
            "such as reasoning, learning, perception, "
            "and language."
        )

    # --------------------------------------------------------
    # System information
    # --------------------------------------------------------

    if (
        "system information" in command
        or "pc specs" in command
        or "computer information" in command
    ):

        return system_information()

    return None


# ============================================================
#                    COMMAND PROCESSOR
# ============================================================

def process_command(command):

    command = command.lower().strip()

    # Remove wake word

    command = re.sub(
        r"^(hey\s+)?obstratum[\s,:-]*",
        "",
        command
    ).strip()

    if not command:

        return "Yes?"

    # ========================================================
    # EXIT
    # ========================================================

    if command in [
        "exit",
        "quit",
        "close",
        "shutdown",
        "goodbye",
        "bye",
    ]:

        return "__EXIT__"

    # ========================================================
    # WEBSITES
    # ========================================================

    for site in WEBSITES:

        if command in [

            f"open {site}",
            f"launch {site}",
            site,

        ]:

            return open_website(
                site
            )

    # ========================================================
    # WINDOWS TOOLS
    # ========================================================

    windows_result = windows_command(
        command
    )

    if windows_result:

        return windows_result

    if command.startswith("open "):

        folder_name = command[
            5:
        ].strip()

        folder_result = open_folder(
            folder_name
        )

        if folder_result:

            return folder_result

    # ========================================================
    # FOLDERS WITHOUT "OPEN"
    # ========================================================

    folder_result = open_folder(
        command
    )

    if folder_result:

        return folder_result

    # ========================================================
    # APPLICATIONS
    # ========================================================

    # Convert aliases

    for alias, actual in ALIASES.items():

        if command in [

            f"open {alias}",
            f"launch {alias}",
            f"start {alias}",

        ]:

            return launch_application(
                actual
            )

    for app in CUSTOM_APPS:

        if command in [

            f"open {app}",
            f"launch {app}",
            f"start {app}",
            app,

        ]:

            return launch_application(
                app
            )

    # ========================================================
    # GOOGLE SEARCH
    # ========================================================

    if command.startswith(
        "search "
    ):

        query = command[
            7:
        ].strip()

        if query:

            return google_search(
                query
            )

    # ========================================================
    # YOUTUBE SEARCH
    # ========================================================

    if command.startswith(
        "youtube search "
    ):

        query = command[
            len("youtube search "):
        ].strip()

        if query:

            return youtube_search(
                query
            )

    # ========================================================
    # PLAY YOUTUBE
    # ========================================================

    if command.startswith(
        "play "
    ):

        query = command[
            5:
        ].strip()

        if query:

            return youtube_search(
                query
            )

    # ========================================================
    # MATH
    # ========================================================

    expression = extract_math(
        command
    )

    if expression:

        result = safe_calculate(
            expression
        )

        if result is not None:

            return (
                f"The answer is {result}."
            )

    # ========================================================
    # BASIC AI
    # ========================================================

    answer = answer_question(
        command
    )

    if answer:

        return answer

    # ========================================================
    # HELP
    # ========================================================

    if command in [
        "help",
        "commands",
        "show commands",
    ]:

        return (
            "Try: open YouTube, open Genshin, "
            "open Edge, open VS Code, "
            "open Downloads, search robotics, "
            "play Genshin music, calculate 25 times 48, "
            "system information, or what time is it."
        )

    # ========================================================
    # UNKNOWN
    # ========================================================

    return (
        "I don't understand that command yet. "
        "Say 'help' to see examples."
    )


# ============================================================
#                   VOICE RECOGNITION
# ============================================================

recognizer = sr.Recognizer()


def record_audio():

    sample_rate = 16000

    duration = 6

    try:

        audio = sd.rec(
            int(
                duration
                * sample_rate
            ),
            samplerate=sample_rate,
            channels=1,
            dtype="int16"
        )

        sd.wait()

        return (
            audio,
            sample_rate
        )

    except Exception as error:

        return (
            None,
            str(error)
        )


def voice_command():

    def worker():

        update_status(
            "🎙️ Listening..."
        )

        audio_data, result = record_audio()

        if audio_data is None:

            update_status(
                "❌ Microphone error"
            )

            add_message(
                "OBSTRATUM",
                "Microphone error: "
                + str(result)
            )

            return

        try:

            update_status(
                "🧠 Understanding..."
            )

            temp_file = tempfile.NamedTemporaryFile(
                suffix=".wav",
                delete=False
            )

            temp_path = temp_file.name

            temp_file.close()

            with wave.open(
                temp_path,
                "wb"
            ) as wav:

                wav.setnchannels(1)

                wav.setsampwidth(2)

                wav.setframerate(
                    result
                )

                wav.writeframes(
                    audio_data.tobytes()
                )

            with sr.AudioFile(
                temp_path
            ) as source:

                audio = recognizer.record(
                    source
                )

            text = recognizer.recognize_google(
                audio
            )

            os.remove(
                temp_path
            )

            root.after(
                0,
                lambda: handle_command(
                    text
                )
            )

        except sr.UnknownValueError:

            update_status(
                "❌ Didn't understand"
            )

        except sr.RequestError:

            update_status(
                "❌ Speech service unavailable"
            )

        except Exception as error:

            update_status(
                "❌ Voice error"
            )

            add_message(
                "OBSTRATUM",
                str(error)
            )

    threading.Thread(
        target=worker,
        daemon=True
    ).start()


# ============================================================
#                         GUI
# ============================================================

root = tk.Tk()

root.title(
    "OBSTRATUM"
)

root.geometry(
    "1000x650"
)

root.minsize(
    750,
    500
)

root.configure(
    bg="#0b0d10"
)


# ============================================================
# HEADER
# ============================================================

header = tk.Frame(
    root,
    bg="#14171c",
    height=85
)

header.pack(
    fill=tk.X
)


title = tk.Label(
    header,
    text="OBSTRATUM",
    font=(
        "Segoe UI",
        27,
        "bold"
    ),
    bg="#14171c",
    fg="white"
)

title.pack(
    pady=(12, 0)
)


subtitle = tk.Label(
    header,
    text=f"Desktop AI Assistant  •  v{VERSION}",
    font=(
        "Segoe UI",
        10
    ),
    bg="#14171c",
    fg="#8b949e"
)

subtitle.pack()


# ============================================================
# CHAT
# ============================================================

chat = scrolledtext.ScrolledText(
    root,
    wrap=tk.WORD,
    font=(
        "Consolas",
        11
    ),
    bg="#0d1117",
    fg="#e6edf3",
    insertbackground="white",
    selectbackground="#264f78",
    borderwidth=0,
    padx=20,
    pady=20
)

chat.pack(
    fill=tk.BOTH,
    expand=True,
    padx=15,
    pady=15
)

chat.config(
    state=tk.DISABLED
)


# ============================================================
# INPUT
# ============================================================

bottom = tk.Frame(
    root,
    bg="#0b0d10"
)

bottom.pack(
    fill=tk.X,
    padx=15,
    pady=(0, 8)
)


input_box = tk.Entry(
    bottom,
    font=(
        "Segoe UI",
        13
    ),
    bg="#171b21",
    fg="white",
    insertbackground="white",
    relief=tk.FLAT
)

input_box.pack(
    side=tk.LEFT,
    fill=tk.X,
    expand=True,
    ipady=12,
    padx=(0, 10)
)

input_box.bind(
    "<Return>",
    lambda event: typed_command()
)


send_button = tk.Button(
    bottom,
    text="SEND",
    command=typed_command,
    font=(
        "Segoe UI",
        10,
        "bold"
    ),
    bg="#2563eb",
    fg="white",
    activebackground="#1d4ed8",
    activeforeground="white",
    relief=tk.FLAT,
    padx=22,
    pady=11
)

send_button.pack(
    side=tk.LEFT,
    padx=(0, 8)
)


voice_button = tk.Button(
    bottom,
    text="🎙️ VOICE",
    command=voice_command,
    font=(
        "Segoe UI",
        10,
        "bold"
    ),
    bg="#20242b",
    fg="white",
    activebackground="#30353e",
    relief=tk.FLAT,
    padx=22,
    pady=11
)

voice_button.pack(
    side=tk.LEFT
)


# ============================================================
# STATUS
# ============================================================

status_label = tk.Label(
    root,
    text="🟢 OBSTRATUM ONLINE",
    font=(
        "Segoe UI",
        9
    ),
    bg="#0b0d10",
    fg="#8b949e"
)

status_label.pack(
    pady=(0, 10)
)


# ============================================================
# GUI FUNCTIONS
# ============================================================

def update_status(text):

    root.after(
        0,
        lambda: status_label.config(
            text=text
        )
    )


def add_message(
    sender,
    message
):

    chat.config(
        state=tk.NORMAL
    )

    if sender == "You":

        chat.insert(
            tk.END,
            f"\nYOU  ›  {message}\n"
        )

    else:

        chat.insert(
            tk.END,
            f"OBSTRATUM  ›  {message}\n"
        )

    chat.see(
        tk.END
    )

    chat.config(
        state=tk.DISABLED
    )


def handle_command(command):

    if not command:

        return

    command = command.strip()

    add_message(
        "You",
        command
    )

    input_box.delete(
        0,
        tk.END
    )

    response = process_command(
        command
    )

    if response == "__EXIT__":

        add_message(
            "OBSTRATUM",
            "Shutting down."
        )

        threading.Thread(
            target=speak,
            args=("Shutting down.",),
            daemon=True
        ).start()

        root.after(
            1000,
            root.destroy
        )

        return

    add_message(
        "OBSTRATUM",
        response
    )

    update_status(
        "🟢 OBSTRATUM ONLINE"
    )

    threading.Thread(
        target=speak,
        args=(response,),
        daemon=True
    ).start()


def typed_command():

    command = input_box.get()

    handle_command(
        command
    )


# ============================================================
# STARTUP
# ============================================================

add_message(
    "OBSTRATUM",
    "Systems online."
)

add_message(
    "OBSTRATUM",
    "Type 'help' for available commands."
)


# ============================================================
# RUN
# ============================================================

root.mainloop()