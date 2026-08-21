# ============================================================
#                     OBSTRATUM V3
#              Windows Desktop AI Assistant
# ============================================================

import tkinter as tk
from tkinter import scrolledtext
import subprocess
import webbrowser
import threading
import os
import re
import ast
import operator
import datetime
import platform
import getpass
import shutil
import urllib.parse

import pyttsx3
import speech_recognition as sr
import sounddevice as sd


# ============================================================
#                         SETTINGS
# ============================================================

ASSISTANT_NAME = "OBSTRATUM"
VERSION = "3.0"

VOICE_RATE = 175
VOICE_VOLUME = 1.0

VOICE_RECORD_SECONDS = 6
VOICE_SAMPLE_RATE = 16000


# ============================================================
#                    APPLICATION CONFIG
# ============================================================
#
# ADD / REMOVE APPS HERE.
#
# Example:
#
# "vlc": r"C:\Program Files\VideoLAN\VLC\vlc.exe",
#
# Then simply say:
#
# "open vlc"
#
# ============================================================

CUSTOM_APPS = {

    # ---------------- WINDOWS ----------------

    "edge": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",

    "vscode": r"F:\Microsoft VS Code\Code.exe",

    "notepad": r"C:\Windows\System32\notepad.exe",

    "calculator": r"C:\Windows\System32\calc.exe",

    "paint": r"C:\Windows\System32\mspaint.exe",

    "cmd": r"C:\Windows\System32\cmd.exe",

    "powershell": r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe",

    "task manager": r"C:\Windows\System32\taskmanager.exe",

    # ---------------- GAMES ----------------

    # ---------------- APPS ----------------
    
}


# ============================================================
#                         WEBSITES
# ============================================================

WEBSITES = {}


# ============================================================
#                         ALIASES
# ============================================================
#
# These are alternative names.
#
# "open visual studio code"
#              ↓
#           vscode
#
# ============================================================

ALIASES = {

}


# ============================================================
#                    TEXT TO SPEECH
# ============================================================

try:

    tts = pyttsx3.init()

    tts.setProperty(
        "rate",
        VOICE_RATE
    )

    tts.setProperty(
        "volume",
        VOICE_VOLUME
    )

    TTS_AVAILABLE = True

except Exception:

    tts = None
    TTS_AVAILABLE = False


tts_lock = threading.Lock()


def speak(text):

    if not TTS_AVAILABLE:
        return

    try:

        with tts_lock:

            tts.say(text)
            tts.runAndWait()

    except Exception:
        pass


# ============================================================
#                       CALCULATOR
# ============================================================

OPERATORS = {

    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.FloorDiv: operator.floordiv,

    ast.USub: operator.neg,
    ast.UAdd: operator.pos,

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

    text = command.lower()

    replacements = {

        "multiplied by": "*",
        "divided by": "/",
        "to the power of": "**",

        "plus": "+",
        "minus": "-",
        "times": "*",
        "divide by": "/",
        "divide": "/",
        "power": "**",

    }

    for word, symbol in replacements.items():

        text = text.replace(
            word,
            symbol
        )

    phrases = [

        "calculate",
        "what is",
        "what's",
        "solve",
        "compute",
        "equals",
        "equal to",

    ]

    for phrase in phrases:

        text = text.replace(
            phrase,
            ""
        )

    expression = re.sub(
        r"[^0-9+\-*/%.() ]",
        "",
        text
    ).strip()

    if not expression:
        return None

    if not re.search(
        r"\d",
        expression
    ):
        return None

    return expression


# ============================================================
#                    APPLICATION FINDER
# ============================================================

def find_application(name):

    # 1. Custom path

    custom_path = CUSTOM_APPS.get(
        name,
        ""
    )

    if custom_path:

        if os.path.isfile(custom_path):

            return custom_path

    # 2. Search Windows PATH

    path = shutil.which(name)

    if path:

        return path

    # 3. Common locations

    username = getpass.getuser()

    possible_paths = [

        rf"C:\Users\{username}\AppData\Local\Programs\{name}\{name}.exe",

        rf"C:\Program Files\{name}\{name}.exe",

        rf"C:\Program Files (x86)\{name}\{name}.exe",

    ]

    for path in possible_paths:

        if os.path.isfile(path):

            return path

    return None


# ============================================================
#                    LAUNCH APPLICATION
# ============================================================

def launch_application(name):

    path = find_application(
        name
    )

    if not path:

        return (
            f"I couldn't find {name}.\n"
            f"Add its .exe path inside CUSTOM_APPS."
        )

    try:

        os.startfile(path)

        return (
            f"Launching {name}."
        )

    except Exception as error:

        return (
            f"I couldn't launch {name}.\n"
            f"Error: {error}"
        )


# ============================================================
#                     WINDOWS TOOLS
# ============================================================

WINDOWS_TOOLS = {

    "file explorer": "explorer",
    "explorer": "explorer",

    "task manager": "taskmgr",

    "control panel": "control",

    "device manager": "devmgmt.msc",

    "disk management": "diskmgmt.msc",

    "services": "services.msc",

    "event viewer": "eventvwr.msc",

    "resource monitor": "resmon",

    "system configuration": "msconfig",

    "registry editor": "regedit",

    "snipping tool": "snippingtool",

    "terminal": "wt",

}


def open_windows_tool(name):

    command = WINDOWS_TOOLS.get(
        name
    )

    if not command:

        return None

    try:

        subprocess.Popen(
            command,
            shell=True
        )

        return (
            f"Opening {name}."
        )

    except Exception as error:

        return (
            f"Couldn't open {name}: {error}"
        )


# ============================================================
#                      WINDOWS SETTINGS
# ============================================================

def open_settings():

    try:

        os.startfile(
            "ms-settings:"
        )

        return "Opening Windows Settings."

    except Exception:

        return "I couldn't open Windows Settings."


# ============================================================
#                        FOLDERS
# ============================================================

def get_folders():

    home = os.path.expanduser(
        "~"
    )

    return {

        "desktop":
            os.path.join(
                home,
                "Desktop"
            ),

        "downloads":
            os.path.join(
                home,
                "Downloads"
            ),

        "documents":
            os.path.join(
                home,
                "Documents"
            ),

        "pictures":
            os.path.join(
                home,
                "Pictures"
            ),

        "videos":
            os.path.join(
                home,
                "Videos"
            ),

        "music":
            os.path.join(
                home,
                "Music"
            ),

    }


def open_folder(name):

    folders = get_folders()

    path = folders.get(
        name
    )

    if not path:

        return None

    if not os.path.exists(path):

        return (
            f"I couldn't find your {name} folder."
        )

    try:

        os.startfile(path)

        return (
            f"Opening {name}."
        )

    except Exception:

        return (
            f"I couldn't open {name}."
        )


# ============================================================
#                         WEBSITES
# ============================================================

def open_website(name):

    url = WEBSITES.get(
        name
    )

    if not url:

        return None

    try:

        webbrowser.open(
            url
        )

        return (
            f"Opening {name}."
        )

    except Exception:

        return (
            f"I couldn't open {name}."
        )


# ============================================================
#                         SEARCH
# ============================================================

def google_search(query):

    encoded = urllib.parse.quote_plus(
        query
    )

    url = (
        "https://www.google.com/search?q="
        + encoded
    )

    webbrowser.open(
        url
    )

    return (
        f"Searching Google for {query}."
    )


def youtube_search(query):

    encoded = urllib.parse.quote_plus(
        query
    )

    url = (
        "https://www.youtube.com/results?search_query="
        + encoded
    )

    webbrowser.open(
        url
    )

    return (
        f"Searching YouTube for {query}."
    )


# ============================================================
#                       SYSTEM INFO
# ============================================================

def system_information():

    username = getpass.getuser()

    computer = platform.node()

    system = platform.system()

    version = platform.version()

    processor = platform.processor()

    return (
        f"USER: {username}\n"
        f"PC: {computer}\n"
        f"OS: {system}\n"
        f"WINDOWS: {version}\n"
        f"CPU: {processor}"
    )


# ============================================================
#                         BASIC AI
# ============================================================

def answer_question(command):

    text = command.lower().strip()

    # Identity

    if (
        "who are you" in text
        or "what are you" in text
    ):

        return (
            "I am OBSTRATUM, "
            "your Python based Windows assistant."
        )

    if "your name" in text:

        return (
            "My name is OBSTRATUM."
        )

    if "who made you" in text:

        return (
            "I was created as the OBSTRATUM "
            "Python project."
        )

    # Greetings

    if text in [
        "hello",
        "hi",
        "hey",
        "hello obstratum",
        "hi obstratum",
    ]:

        return (
            "Hello. OBSTRATUM is online."
        )

    if "how are you" in text:

        return (
            "All systems are operational."
        )

    # Capabilities

    if "what can you do" in text:

        return (
            "I can launch applications and games, "
            "open websites, search Google and YouTube, "
            "perform calculations, open Windows tools, "
            "open folders, provide system information, "
            "and respond to voice commands."
        )

    # Time

    if (
        "what time" in text
        or text == "time"
    ):

        now = datetime.datetime.now()

        return (
            "The current time is "
            + now.strftime("%I:%M %p")
        )

    # Date

    if (
        "what date" in text
        or "today's date" in text
        or text == "date"
    ):

        now = datetime.datetime.now()

        return (
            "Today is "
            + now.strftime("%d %B %Y")
        )

    # Python

    if "what is python" in text:

        return (
            "Python is a high level programming "
            "language widely used for software, "
            "automation, artificial intelligence, "
            "data science and robotics."
        )

    # AI

    if (
        "what is artificial intelligence"
        in text
    ):

        return (
            "Artificial intelligence is the field "
            "of building computer systems capable "
            "of performing tasks that normally "
            "require forms of human intelligence."
        )

    # System

    if (
        "system information" in text
        or "pc specs" in text
        or "computer information" in text
    ):

        return system_information()

    return None


# ============================================================
#                       COMMAND ENGINE
# ============================================================

def process_command(command):

    text = command.lower().strip()

    # Remove wake word

    text = re.sub(
        r"^(hey\s+)?obstratum[\s,:-]*",
        "",
        text
    ).strip()

    if not text:

        return "Yes?"

    # ========================================================
    # EXIT
    # ========================================================

    if text in [
        "exit",
        "quit",
        "close",
        "shutdown",
        "goodbye",
        "bye",
    ]:

        return "__EXIT__"

    # ========================================================
    # SETTINGS
    # ========================================================

    if text in [
        "open settings",
        "open windows settings",
        "settings",
    ]:

        return open_settings()

    # ========================================================
    # WINDOWS TOOLS
    # ========================================================

    for name in WINDOWS_TOOLS:

        if text in [
            name,
            f"open {name}",
            f"launch {name}",
            f"start {name}",
        ]:

            result = open_windows_tool(
                name
            )

            if result:

                return result

    # ========================================================
    # WEBSITES
    # ========================================================

    for website in WEBSITES:

        if text in [
            website,
            f"open {website}",
            f"launch {website}",
            f"start {website}",
        ]:

            result = open_website(
                website
            )

            if result:

                return result

    # ========================================================
    # FOLDERS
    # ========================================================

    folders = get_folders()

    for folder in folders:

        if text in [
            folder,
            f"open {folder}",
        ]:

            result = open_folder(
                folder
            )

            if result:

                return result

    # ========================================================
    # APPLICATION ALIASES
    # ========================================================

    for alias, application in ALIASES.items():

        if text in [
            alias,
            f"open {alias}",
            f"launch {alias}",
            f"start {alias}",
        ]:

            return launch_application(
                application
            )

    # ========================================================
    # CUSTOM APPLICATIONS
    # ========================================================

    for application in CUSTOM_APPS:

        if text in [
            application,
            f"open {application}",
            f"launch {application}",
            f"start {application}",
        ]:

            return launch_application(
                application
            )

    # ========================================================
    # GOOGLE SEARCH
    # ========================================================

    if text.startswith(
        "search "
    ):

        query = text[
            len("search "):
        ].strip()

        if query:

            return google_search(
                query
            )

    # ========================================================
    # YOUTUBE SEARCH
    # ========================================================

    if text.startswith(
        "youtube search "
    ):

        query = text[
            len("youtube search "):
        ].strip()

        if query:

            return youtube_search(
                query
            )

    # ========================================================
    # PLAY
    # ========================================================

    if text.startswith(
        "play "
    ):

        query = text[
            len("play "):
        ].strip()

        if query:

            return youtube_search(
                query
            )

    # ========================================================
    # CALCULATOR
    # ========================================================

    expression = extract_math(
        text
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
        text
    )

    if answer:

        return answer

    # ========================================================
    # HELP
    # ========================================================

    if text in [
        "help",
        "commands",
        "show commands",
    ]:

        return (
            "Examples:\n\n"
            "open youtube\n"
            "open youtube music\n"
            "open edge\n"
            "open vscode\n"
            "open genshin\n"
            "open ghost of tsushima\n"
            "open downloads\n"
            "open task manager\n"
            "open settings\n"
            "search robotics\n"
            "youtube search python AI\n"
            "play Genshin music\n"
            "calculate 25 times 48\n"
            "what time is it\n"
            "system information"
        )

    # ========================================================
    # UNKNOWN
    # ========================================================

    return (
        "I don't understand that command yet.\n"
        "Type 'help' to see what I can do."
    )


# ============================================================
#                       VOICE SYSTEM
# ============================================================

recognizer = sr.Recognizer()


def listen_for_voice():

    try:

        update_status(
            "🎙️ Listening..."
        )

        recording = sd.rec(
            int(
                VOICE_RECORD_SECONDS
                * VOICE_SAMPLE_RATE
            ),
            samplerate=VOICE_SAMPLE_RATE,
            channels=1,
            dtype="int16"
        )

        sd.wait()

        update_status(
            "🧠 Processing voice..."
        )

        # Convert directly to SpeechRecognition AudioData.
        # No PyAudio and no temporary WAV file required.

        audio_data = sr.AudioData(
            recording.tobytes(),
            VOICE_SAMPLE_RATE,
            2
        )

        text = recognizer.recognize_google(
            audio_data
        )

        return text

    except sr.UnknownValueError:

        return (
            None,
            "I couldn't understand the voice command."
        )

    except sr.RequestError:

        return (
            None,
            "The speech recognition service is unavailable."
        )

    except Exception as error:

        return (
            None,
            f"Microphone error: {error}"
        )


def voice_command():

    if voice_button["state"] == tk.DISABLED:

        return

    voice_button.config(
        state=tk.DISABLED
    )

    def worker():

        result = listen_for_voice()

        if isinstance(
            result,
            tuple
        ):

            text, error = result

        else:

            text = result
            error = None

        root.after(
            0,
            lambda: finish_voice(
                text,
                error
            )
        )

    threading.Thread(
        target=worker,
        daemon=True
    ).start()


def finish_voice(
    text,
    error
):

    voice_button.config(
        state=tk.NORMAL
    )

    if error:

        add_message(
            "OBSTRATUM",
            error
        )

        update_status(
            "🟢 Ready"
        )

        return

    if text:

        handle_command(
            text
        )

    else:

        update_status(
            "🟢 Ready"
        )


# ============================================================
#                           GUI
# ============================================================

root = tk.Tk()

root.title(
    f"{ASSISTANT_NAME} V{VERSION}"
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
#                         HEADER
# ============================================================

header = tk.Frame(
    root,
    bg="#15181e",
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
    bg="#15181e",
    fg="white"
)

title.pack(
    pady=(12, 0)
)


subtitle = tk.Label(
    header,
    text=f"Desktop AI Assistant  •  Version {VERSION}",
    font=(
        "Segoe UI",
        10
    ),
    bg="#15181e",
    fg="#8b949e"
)

subtitle.pack()


# ============================================================
#                          CHAT
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
#                       INPUT AREA
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


# ============================================================
#                  COMMAND FUNCTIONS
# ============================================================

def update_status(text):

    status_label.config(
        text=text
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

    command = command.strip()

    if not command:

        return

    add_message(
        "You",
        command
    )

    input_box.delete(
        0,
        tk.END
    )

    update_status(
        "⚙️ Working..."
    )

    def worker():

        response = process_command(
            command
        )

        root.after(
            0,
            lambda: finish_command(
                response
            )
        )

    threading.Thread(
        target=worker,
        daemon=True
    ).start()


def finish_command(response):

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


def typed_command(event=None):

    command = input_box.get().strip()

    if command:

        handle_command(
            command
        )


# ============================================================
#                      SEND BUTTON
# ============================================================

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


# ============================================================
#                     VOICE BUTTON
# ============================================================

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
    activeforeground="white",
    relief=tk.FLAT,
    padx=22,
    pady=11
)

voice_button.pack(
    side=tk.LEFT
)


# ============================================================
#                         STATUS
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
#                    ENTER KEY SUPPORT
# ============================================================

input_box.bind(
    "<Return>",
    typed_command
)


# ============================================================
#                     STARTUP MESSAGE
# ============================================================

add_message(
    "OBSTRATUM",
    "Systems online."
)

add_message(
    "OBSTRATUM",
    "Type 'help' to see available commands."
)


# Put cursor in command box

input_box.focus()


# ============================================================
#                         RUN
# ============================================================

root.mainloop()